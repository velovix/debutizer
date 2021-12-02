from pathlib import Path

from debutizer.errors import UnexpectedError


class Environment:
    """Describes the environment wherein a package is being processed"""

    def __init__(
        self,
        codename: str,
        architecture: str,
        package_root: Path,
        build_root: Path,
        artifacts_root: Path,
        network_access: bool = False,
    ):
        self._codename = codename
        self._architecture = architecture
        self._package_root = package_root
        self._build_root = build_root
        self._artifacts_root = artifacts_root
        self._network_access = network_access

    @property
    def codename(self) -> str:
        """The distribution codename, like 'focal'"""
        return self._codename

    @property
    def architecture(self) -> str:
        """The target CPU architecture"""
        return self._architecture

    @property
    def package_root(self) -> Path:
        """A directory containing directories for each package, with a package.py
        inside
        """
        return self._package_root

    @property
    def build_root(self) -> Path:
        """A directory for holding intermediate build artifacts"""
        return self._build_root

    @property
    def artifacts_root(self) -> Path:
        """A directory where build results should be stored"""
        return self._artifacts_root

    @property
    def network_access(self) -> bool:
        """If True, the build will be provided network access. Note that Debian's
        official package building infrastructure does not provide network access.
        """
        return self._network_access

    @network_access.setter
    def network_access(self, value: bool) -> None:
        self._network_access = value

    def compat_version(self) -> str:
        """
        :return: the debhelper compatibility version used by the current distribution
        """

        if self._codename in ["bionic"]:
            return "11"
        elif self._codename in ["focal", "buster"]:
            return "12"
        elif self._codename in ["groovy", "hirsute", "impish", "bullseye"]:
            return "13"
        else:
            raise UnexpectedError(f"Unknown distribution: {self._codename}")
