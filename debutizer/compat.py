from pathlib import Path
from typing import Optional

from .environment import Environment
from .errors import CommandError, UnexpectedError


class Compat:
    version: Optional[int]

    def __init__(self, package_dir: Path):
        self.version = None
        self._package_dir = package_dir

    def from_distribution(self) -> None:
        """Use the debhelper compatibility version used by the current distribution"""
        if Environment.codename is None:
            raise UnexpectedError("The Environment.codename field must be set")

        if Environment.codename in ["bionic"]:
            self.version = 11
        elif Environment.codename in ["focal", "buster"]:
            self.version = 12
        elif Environment.codename in ["groovy", "hirsute", "impish", "bullseye"]:
            self.version = 13
        else:
            raise UnexpectedError(f"Unknown distribution: {Environment.codename}")

        self.save()

    def load(self, complete: bool):
        compat_file = self._package_dir / "debian" / "compat"

        if compat_file.is_file():
            compat_str = compat_file.read_text().strip()
            try:
                self.version = int(compat_str)
            except ValueError as ex:
                raise CommandError(f"While parsing the compat file: {ex}") from ex

    def save(self):
        if self.version is not None:
            compat_file = self._package_dir / "debian" / "compat"
            compat_file.write_text(str(self.version))
