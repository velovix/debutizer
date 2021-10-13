from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from ..version import Version


class Upstream(ABC):
    """A way of retrieving source code and potentially package configuration from some
    source.
    """

    package_root: ClassVar[Path]
    build_root: ClassVar[Path]

    name: str
    version: Version

    def __init__(self, *, name: str, version: Version):
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
            self.build_root / self.name / f"{self.name}-{self.version.upstream_version}"
        )
