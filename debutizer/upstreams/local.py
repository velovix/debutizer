import shutil
from pathlib import Path
from typing import List, Optional

from ..commands.utils import make_source_archive
from ..errors import CommandError
from ..subprocess_utils import run
from ..version import Version
from .base import Upstream


class LocalUpstream(Upstream):
    """An upstream that gets source from a local directory"""

    path: Path

    def __init__(
        self,
        *,
        name: str,
        version: Version,
        path: Path,
        excluded_paths: Optional[List[Path]] = None,
    ):
        super().__init__(name=name, version=version)

        if excluded_paths is None:
            excluded_paths = []

        self.path = path
        if not self.path.is_dir():
            raise CommandError(f"Local path '{self.path}' does not exist")
        self.excluded_paths = excluded_paths

    def fetch(self) -> Path:
        build_dir = self.build_root / self.name
        build_dir.mkdir()
        package_dir = self._package_dir()

        shutil.copytree(self.path, package_dir)
        for excluded_path in self.excluded_paths:
            excluded_path = package_dir / excluded_path
            if excluded_path.is_dir():
                shutil.rmtree(excluded_path)
            elif excluded_path.is_file():
                excluded_path.unlink()

        # Create the source archive in the previous directory
        make_source_archive(
            package_dir=package_dir,
            destination_dir=build_dir,
            name=self.name,
            version=self.version,
        )

        # Copy the debian/ directory, if one is provided
        debian_path = self.package_root / self.name / "debian"
        if debian_path.is_dir():
            shutil.copytree(debian_path, package_dir / "debian")

        return package_dir
