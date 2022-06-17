from pathlib import Path

from ._containers import NewlineSeparatedFile


class ConfFiles(NewlineSeparatedFile[Path]):
    def __init__(self, package_dir: Path) -> None:
        super().__init__(package_dir / self._PATH, create_func=Path)

    _PATH = Path("debian/conffiles")
