from abc import ABC, abstractmethod
from pathlib import Path

from ..environment import Environment
from ..version import Version


class Upstream(ABC):
    """A way of retrieving source code and potentially package configuration from some
    source.
    """

    name: str
    version: Version

    def __init__(self, *, env: Environment, name: str, version: Version):
        self.env = env
        self.name = name
        self.version = version

    @abstractmethod
    def fetch(self) -> Path:
        """Retrieves data from the upstream source.

        :return: The directory with upstream source and potentially a debian/ folder
        """
        ...

    def _package_dir(self) -> Path:
        return (
            self.env.build_root
            / self.name
            / f"{self.name}-{self.version.upstream_version}"
        )
