from pathlib import Path

from ._list_backed_container import ListBackedContainer


class ConfFiles(ListBackedContainer[Path]):
    def __init__(self, package_dir: Path) -> None:
        super().__init__()
        self._package_dir = package_dir

    def add(self, path: Path) -> None:
        self._data.append(path)

    def save(self) -> None:
        if len(self) > 0:
            conffiles_file = self._package_dir / self._PATH
            content = "\n".join(str(p) for p in self)
            conffiles_file.write_text(content)

    def load(self) -> None:
        conffiles_file = self._package_dir / self._PATH
        if conffiles_file.is_file():
            path_strs = conffiles_file.read_text().split("\n")
            self._data = [Path(s) for s in path_strs]

    _PATH = Path("debian/conffiles")
