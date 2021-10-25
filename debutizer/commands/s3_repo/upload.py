import argparse
import base64
import hashlib
import hmac
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from time import sleep
from typing import List
from urllib.parse import urlparse

import requests

from debutizer.errors import CommandError
from debutizer.print_utils import Color, Format, print_color, print_done

from ..artifacts import find_archives
from ..command import Command


class UploadCommand(Command):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="debutizer s3-repo upload",
            description="Uploads files in the archive directory to the S3-compatible "
            "bucket",
        )

        self.add_archive_args()

        self.parser.add_argument(
            "--endpoint",
            type=str,
            required=True,
            help="The name of the S3-compatible endpoint. For AWS, this is "
            "https://s3.amazonaws.com",
        )
        self.parser.add_argument(
            "--bucket",
            type=str,
            required=True,
            help="The name of the bucket to upload to",
        )
        self.parser.add_argument(
            "--access-key",
            type=str,
            required=True,
            help="The access key for this bucket",
        )
        self.parser.add_argument(
            "--secret-key",
            type=str,
            required=True,
            help="The secret key for this bucket",
        )

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[3:])

    def behavior(self, args: argparse.Namespace) -> None:
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
            print(f"Uploading {artifact_file_path}...")
            _upload_artifact(
                bucket_endpoint=bucket_endpoint,
                access_key=args.access_key,
                secret_key=args.secret_key,
                artifacts_dir=args.artifacts_dir,
                artifact_file_path=artifact_file_path,
            )

        with tempfile.TemporaryDirectory() as mount_path, _mount_s3fs(
            endpoint=endpoint.geturl(),
            bucket=args.bucket,
            access_key=args.access_key,
            secret_key=args.secret_key,
            mount_path=Path(mount_path),
        ):
            print("")
            print_color(
                "Updating the Packages file",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )
            metadata_files += _update_packages_file(args.artifacts_dir)

            print("")
            print_color(
                "Updating the Sources file",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )
            metadata_files += _update_sources_file(args.artifacts_dir)

        for metadata_file in metadata_files:
            _upload_artifact(
                bucket_endpoint=bucket_endpoint,
                access_key=args.access_key,
                secret_key=args.secret_key,
                artifacts_dir=args.artifacts_dir,
                artifact_file_path=metadata_file,
            )

        print("")
        print_done("Upload")


def _upload_artifact(
    bucket_endpoint: str,
    access_key: str,
    secret_key: str,
    artifacts_dir: Path,
    artifact_file_path: Path,
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
        },
    )
    prepared = request.prepare()

    hmac_message = (
        prepared.method
        + "\n"
        + prepared.headers["Content-MD5"]
        + "\n"
        + prepared.headers["Content-Type"]
        + "\n"
        + prepared.headers["Date"]
        + "\n"
        + urlparse(prepared.url).path
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
    _, passwd_path = tempfile.mkstemp()
    try:
        with Path(passwd_path).open("w") as f:
            f.write(f"{access_key}:{secret_key}")

        subprocess.run(
            [
                "s3fs",
                str(mount_path),
                "-o",
                f"passwd_file={passwd_path}",
                "-o",
                f"url={endpoint}",
                "-o",
                f"bucket={bucket}",
                "-o",
                "use_path_request_style",
            ],
            check=True,
        )

        try:
            yield
        finally:
            # Avoids a "device or resource busy" error
            sleep(5)

            subprocess.run(
                ["umount", str(mount_path)],
                check=True,
            )
    finally:
        os.remove(passwd_path)


def _update_packages_file(artifacts_dir: Path) -> List[Path]:
    packages_files = []

    dirs = artifacts_dir.glob("dists/*/*/binary-*")
    dirs = [d.relative_to(artifacts_dir) for d in dirs]

    for dir_ in dirs:
        result = subprocess.run(
            [
                "dpkg-scanpackages",
                "--multiversion",
                dir_,
            ],
            cwd=artifacts_dir,
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        packages_file = artifacts_dir / dir_ / "Packages"
        packages_file.write_text(result.stdout)
        packages_files.append(packages_file)

    return packages_files


def _update_sources_file(artifacts_dir: Path) -> List[Path]:
    sources_files = []

    dirs = artifacts_dir.glob("dists/*/*/source")
    dirs = [d.relative_to(artifacts_dir) for d in dirs]

    for dir_ in dirs:
        result = subprocess.run(
            [
                "dpkg-scansources",
                dir_,
            ],
            cwd=artifacts_dir,
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        sources_file = artifacts_dir / dir_ / "Sources"
        sources_file.write_text(result.stdout)
        sources_files.append(sources_file)

    return sources_files


_SUPPORTED_SCHEMES = ["http", "https"]
