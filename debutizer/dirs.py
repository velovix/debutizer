from pathlib import Path

from ._containers import NewlineSeparatedFile


class Dirs(NewlineSeparatedFile[Path]):
    def __init__(self, package_dir: Path) -> None:
        super().__init__(package_dir / self.FILE_PATH, create_func=Path)

    FILE_PATH = Path("debian/dirs")
