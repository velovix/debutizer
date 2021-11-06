import argparse
import base64
import hashlib
import hmac
import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from time import sleep
from urllib.parse import urlparse

import requests

from debutizer.errors import CommandError, UnexpectedError
from debutizer.print_utils import print_color, print_done
from debutizer.subprocess_utils import run

from ..artifacts import find_archives
from ..command import Command
from ..config import EnvArgumentParser
from ..repo_metadata import add_packages_files, add_release_files, add_sources_files
from ..utils import temp_file


class UploadCommand(Command):
    def __init__(self):
        self.parser = EnvArgumentParser(
            prog="debutizer s3-repo upload",
            description="Uploads files in the archive directory to the S3-compatible "
            "bucket",
        )

        self.add_archive_args()

        self.parser.add_env_flag(
            "--endpoint",
            type=str,
            required=True,
            help="The name of the S3-compatible endpoint. For AWS, this is "
            "https://s3.amazonaws.com",
        )
        self.parser.add_env_flag(
            "--bucket",
            type=str,
            required=True,
            help="The name of the bucket to upload to",
        )
        self.parser.add_env_flag(
            "--access-key",
            type=str,
            required=True,
            help="The access key for this bucket",
        )
        self.parser.add_env_flag(
            "--secret-key",
            type=str,
            required=True,
            help="The secret key for this bucket",
        )
        self.parser.add_env_flag(
            "--sign",
            action="store_true",
            help="If provided, the Release files will be signed. If --gpg-key-id is "
            "provided, that key will be used. Otherwise, the GPG key stored in the "
            "$GPG_SIGNING_KEY environment variable will be added to your keyring and "
            "used. If your key has a password, store it in the $GPG_PASSWORD "
            "environment variable.",
        )
        self.parser.add_env_flag(
            "--gpg-key-id",
            type=str,
            required=False,
            help="The ID of the GPG key in your keyring to sign Release files with",
        )
        self.parser.add_env_flag(
            "--cache-control",
            type=str,
            default="public, max-age=3600",
            help="The Cache-Control value to use for package files. Metadata files, "
            "like Package, will always have a value of 'no-cache' since they are "
            "changed regularly.",
        )

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[3:])

    def behavior(self, args: argparse.Namespace) -> None:
        if (
            args.sign
            and args.gpg_key_id is None
            and "GPG_SIGNING_KEY" not in os.environ
        ):
            raise CommandError(
                "When signing is enabled, either the --gpg-key-id flag or "
                "$GPG_SIGNING_KEY environment variable must be set"
            )

        endpoint = urlparse(args.endpoint)
        if endpoint.scheme not in _SUPPORTED_SCHEMES:
            raise CommandError(
                f"Unsupported scheme {endpoint.scheme}, must be one of "
                f"{_SUPPORTED_SCHEMES}"
            )
        if endpoint.path.endswith("/"):
            endpoint.path = endpoint.path[:-1]

        bucket_endpoint = f"{endpoint.geturl()}/{args.bucket}"

        artifacts = find_archives(args.artifacts_dir, recursive=True)

        metadata_files = []
        for artifact_file_path in artifacts:
            print_color(f"Uploading {artifact_file_path}...")
            _upload_artifact(
                bucket_endpoint=bucket_endpoint,
                access_key=args.access_key,
                secret_key=args.secret_key,
                artifacts_dir=args.artifacts_dir,
                artifact_file_path=artifact_file_path,
                cache_control=args.cache_control,
            )

        with tempfile.TemporaryDirectory() as mount_path_name, _mount_s3fs(
            endpoint=endpoint.geturl(),
            bucket=args.bucket,
            access_key=args.access_key,
            secret_key=args.secret_key,
            mount_path=Path(mount_path_name),
        ):
            mount_path = Path(mount_path_name)
            metadata_files += add_packages_files(mount_path)
            metadata_files += add_sources_files(mount_path)
            metadata_files += add_release_files(mount_path, args.sign, args.gpg_key_id)

        for metadata_file in metadata_files:
            _upload_artifact(
                bucket_endpoint=bucket_endpoint,
                access_key=args.access_key,
                secret_key=args.secret_key,
                artifacts_dir=args.artifacts_dir,
                artifact_file_path=metadata_file,
                # Metadata files update often
                cache_control="no-cache",
            )

        print_color("")
        print_done("Upload")


def _upload_artifact(
    bucket_endpoint: str,
    access_key: str,
    secret_key: str,
    artifacts_dir: Path,
    artifact_file_path: Path,
    cache_control: str,
) -> None:
    key = str(artifact_file_path.relative_to(artifacts_dir))

    artifact_bytes = artifact_file_path.read_bytes()
    md5_hash = base64.b64encode(hashlib.md5(artifact_bytes).digest()).decode()

    request = requests.Request(
        "PUT",
        f"{bucket_endpoint}/{key}",
        data=artifact_bytes,
        headers={
            "Date": format_datetime(datetime.now(timezone.utc), usegmt=True),
            "Content-Type": "application/octet-stream",
            "Content-MD5": md5_hash,
            "Cache-Control": cache_control,
        },
    )
    prepared = request.prepare()
    if prepared.method is None:
        raise UnexpectedError("Prepared request has a method type of None")
    path = urlparse(prepared.url).path
    if isinstance(path, bytes):
        path = path.decode()

    hmac_message = (
        prepared.method
        + "\n"
        + prepared.headers["Content-MD5"]
        + "\n"
        + prepared.headers["Content-Type"]
        + "\n"
        + prepared.headers["Date"]
        + "\n"
        + path
    )

    signature = hmac.new(
        secret_key.encode(),
        hmac_message.encode(),
        digestmod=hashlib.sha1,
    )
    signature_str = base64.b64encode(signature.digest()).decode().rstrip("\n")
    prepared.headers["Authorization"] = f"AWS {access_key}:{signature_str}"

    with requests.Session() as session:
        try:
            response = session.send(prepared)
        except requests.RequestException as ex:
            raise CommandError(f"Error while contacting bucket API: {ex}") from ex

    if not response.ok:
        raise CommandError(
            f"Bad response while uploading to bucket: "
            f"(Status code: {response.status_code}) {response.text}"
        )


@contextmanager
def _mount_s3fs(
    endpoint: str, bucket: str, access_key: str, secret_key: str, mount_path: Path
):
    with temp_file(f"{access_key}:{secret_key}") as password_path:
        run(
            [
                "s3fs",
                mount_path,
                "-o",
                f"passwd_file={password_path}",
                "-o",
                f"url={endpoint}",
                "-o",
                f"bucket={bucket}",
                "-o",
                "use_path_request_style",
            ],
            on_failure="Failed to mount the bucket",
        )

        try:
            yield
        finally:
            # Avoids a "device or resource busy" error
            sleep(5)

            run(
                ["umount", mount_path],
                on_failure="Failed to unmount the bucket",
            )


_SUPPORTED_SCHEMES = ["http", "https"]
