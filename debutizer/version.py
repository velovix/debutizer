from typing import Optional

from debian import debian_support

from .errors import CommandError


class Version:
    epoch: Optional[str]
    upstream_version: str
    debian_revision: str
    full_version: str

    def __init__(
        self,
        *,
        epoch: Optional[str],
        upstream_version: str,
        debian_revision: str,
        full_version: str,
    ):
        self.epoch = epoch
        self.upstream_version = upstream_version
        self.debian_revision = debian_revision
        self.full_version = full_version

    @staticmethod
    def from_string(version: str) -> "Version":
        match = debian_support.Version.re_valid_version.match(version)
        if match is None:
            raise CommandError(
                f"Version string '{version}' is in an invalid format. "
                f"{_FORMAT_DESCRIPTION}"
            )

        epoch = match.group("epoch")
        upstream_version = match.group("upstream_version")
        if upstream_version is None:
            raise CommandError(
                f"Version string '{version}' is missing an upstream version section. "
                f"{_FORMAT_DESCRIPTION}"
            )
        debian_revision = match.group("debian_revision")
        if debian_revision is None:
            raise CommandError(
                f"Version string '{version}' is missing a Debian revision section. "
                f"{_FORMAT_DESCRIPTION}"
            )

        return Version(
            epoch=epoch,
            upstream_version=upstream_version,
            debian_revision=match.group("debian_revision"),
            full_version=version,
        )

    def __str__(self) -> str:
        return self.full_version


_FORMAT_DESCRIPTION = (
    "Versions must follow the format: "
    "[optional epoch]:[upstream version]-[debian revision]"
)
