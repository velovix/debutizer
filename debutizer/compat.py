from pathlib import Path
from typing import Optional

from .errors import CommandError


class Compat:
    version: Optional[str]

    def __init__(self, package_dir: Path):
        self.version = None
        self._package_dir = package_dir

    def load(self, complete: bool):
        compat_file = self._package_dir / "debian" / "compat"

        if compat_file.is_file():
            compat_str = compat_file.read_text().strip()
            try:
                self.version = compat_str
            except ValueError as ex:
                raise CommandError(f"While parsing the compat file: {ex}") from ex

    def save(self):
        if self.version is not None:
            compat_file = self._package_dir / "debian" / "compat"
            compat_file.write_text(self.version)
