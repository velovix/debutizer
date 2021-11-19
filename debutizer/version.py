from typing import Optional

from debian import debian_support

from .errors import CommandError


class Version:
    def __init__(
        self,
        *,
        epoch: Optional[str],
        upstream_version: str,
        debian_revision: Optional[str],
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

        upstream_version = match.group("upstream_version")
        if upstream_version is None:
            raise CommandError(
                f"Version string '{version}' is missing an upstream version section. "
                f"{_FORMAT_DESCRIPTION}"
            )

        return Version(
            epoch=match.group("epoch"),
            upstream_version=upstream_version,
            debian_revision=match.group("debian_revision"),
            full_version=version,
        )

    def __repr__(self):
        return (
            f"Version("
            f"epoch={self.epoch}, "
            f"upstream_version={self.upstream_version}, "
            f"debian_revision={self.debian_revision}, "
            f"full_version={self.full_version}"
            f")"
        )

    def __str__(self) -> str:
        return self.full_version

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        return (
            self.epoch == other.epoch
            and self.upstream_version == other.upstream_version
            and self.debian_revision == other.debian_revision
            and self.full_version == other.full_version
        )


_FORMAT_DESCRIPTION = (
    "Versions must follow the format: "
    "[optional epoch]:[upstream version]-[optional debian revision]"
)
