from pathlib import Path

from debutizer.errors import UnexpectedError


class Environment:
    def __init__(
        self,
        codename: str,
        architecture: str,
        package_root: Path,
        build_root: Path,
        artifacts_root: Path,
    ):
        self.codename = codename
        """The distribution codename, like 'focal'"""
        self.architecture = architecture
        """The target CPU architecture"""
        self.package_root = package_root
        """A directory containing directories for each package, with a package.py
        inside
        """
        self.build_root = build_root
        """A directory for holding intermediate build artifacts"""
        self.artifacts_root = artifacts_root
        """A directory where build results should be stored"""

    def compat_version(self) -> str:
        """
        :return: the debhelper compatibility version used by the current distribution
        """

        if self.codename in ["bionic"]:
            return "11"
        elif self.codename in ["focal", "buster"]:
            return "12"
        elif self.codename in ["groovy", "hirsute", "impish", "bullseye"]:
            return "13"
        else:
            raise UnexpectedError(f"Unknown distribution: {self.codename}")
