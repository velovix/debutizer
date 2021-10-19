import shutil
from pathlib import Path

from ..errors import CommandError
from ..subprocess_utils import run
from ..version import Version
from .base import Upstream


class LocalUpstream(Upstream):
    """An upstream that gets source from a local directory"""

    path: Path

    def __init__(self, *, name: str, version: Version, path: Path):
        super().__init__(name=name, version=version)

        self.path = path
        if not self.path.is_dir():
            raise CommandError(f"Local path '{self.path}' does not exist")

    def fetch(self) -> Path:
        build_dir = self.build_root / self.name
        build_dir.mkdir()
        package_dir = self._package_dir()

        shutil.copytree(self.path, package_dir)

        # Create the source archive in the previous directory
        run(
            [
                "tar",
                "--create",
                "--gzip",
                f"--file={self.name}_{self.version.upstream_version}.orig.tar.gz",
                f"--directory={build_dir}",
                str(package_dir.relative_to(build_dir)),
            ],
            on_failure="Failed to compress the local source",
            cwd=build_dir,
        )

        # Copy the debian/ directory, if one is provided
        debian_path = self.package_root / self.name / "debian"
        if debian_path.is_dir():
            shutil.copytree(debian_path, package_dir / "debian")

        return package_dir
