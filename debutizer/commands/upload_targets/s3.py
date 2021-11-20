import base64
import hashlib
import hmac
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from time import sleep
from typing import Optional, cast
from urllib.parse import urlparse

import requests

from debutizer.commands.artifacts import find_artifacts
from debutizer.commands.config_file import S3Configuration
from debutizer.commands.repo_metadata import (
    add_packages_files,
    add_release_files,
    add_sources_files,
)
from debutizer.commands.upload_targets import UploadTarget
from debutizer.commands.utils import temp_file
from debutizer.errors import CommandError, UnexpectedError
from debutizer.print_utils import print_color, print_notify
from debutizer.subprocess_utils import run


class S3UploadTarget(UploadTarget):
    """Uploads source and binary packages to an S3-compatible bucket"""

    def __init__(self, config: S3Configuration):
        self._config = config

    def upload(self, artifacts_dir: Path) -> None:
        # check_validity ensures these aren't null, but mypy can't figure that out
        access_key: str = cast(str, self._config.access_key)
        secret_key: str = cast(str, self._config.secret_key)

        endpoint = urlparse(self._config.endpoint)
        if endpoint.scheme not in _SUPPORTED_SCHEMES:
            raise CommandError(
                f"Unsupported scheme {endpoint.scheme}, must be one of "
                f"{_SUPPORTED_SCHEMES}"
            )
        url = endpoint.geturl()
        if url.endswith("/"):
            url = url[:-1]

        bucket_endpoint = f"{url}/{self._config.bucket}"

        artifacts = find_artifacts(artifacts_dir, recursive=True)
        for artifact_file_path in artifacts:
            print_color(f"Uploading {artifact_file_path.relative_to(artifacts_dir)}...")
            _upload_artifact(
                prefix=self._config.prefix,
                bucket_endpoint=bucket_endpoint,
                access_key=access_key,
                secret_key=secret_key,
                artifacts_dir=artifacts_dir,
                artifact_file_path=artifact_file_path,
                cache_control=self._config.cache_control,
            )

        with tempfile.TemporaryDirectory() as mount_path_name, _mount_s3fs(
            endpoint=endpoint.geturl(),
            bucket=self._config.bucket,
            access_key=access_key,
            secret_key=secret_key,
            mount_path=Path(mount_path_name),
        ):
            mount_path = Path(mount_path_name)
            print_notify("Updating metadata files...")
            metadata_files = add_packages_files(mount_path)
            metadata_files += add_sources_files(mount_path)
            metadata_files += add_release_files(
                mount_path,
                sign=self._config.sign,
                gpg_key_id=self._config.gpg_key_id,
                gpg_signing_key=self._config.gpg_signing_key,
                gpg_signing_password=self._config.gpg_signing_password,
            )

            # Upload the files to the bucket. S3FS should take care of this, but we need
            # to do it again manually in order to set the Cache-Control header.
            for metadata_file in metadata_files:
                _upload_artifact(
                    prefix=self._config.prefix,
                    bucket_endpoint=bucket_endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    artifacts_dir=mount_path,
                    artifact_file_path=metadata_file,
                    # Metadata files update often
                    cache_control="no-cache",
                )


def _upload_artifact(
    prefix: Optional[str],
    bucket_endpoint: str,
    access_key: str,
    secret_key: str,
    artifacts_dir: Path,
    artifact_file_path: Path,
    cache_control: str,
) -> None:
    key = str(artifact_file_path.relative_to(artifacts_dir))
    if prefix is not None:
        key = f"{prefix}/{key}"

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
