import shutil
from pathlib import Path

from ..subprocess_utils import run
from ..version import Version
from .base import Upstream


class SourceRepositoryUpstream(Upstream):
    """An upstream that clones source code from Git"""

    repository_url: str
    revision_format: str

    def __init__(
        self, *, name: str, version: Version, repository_url: str, revision_format: str
    ):
        super().__init__(name=name, version=version)
        self.repository_url = repository_url
        self.revision_format = revision_format

    def fetch(self) -> Path:
        revision = self.revision_format.format(
            upstream_version=self.version.upstream_version
        )

        build_dir = self.build_root / self.name
        build_dir.mkdir()
        package_dir = self._package_dir()

        # Clone the upstream source
        run(
            [
                "git",
                "clone",
                "--depth=1",
                "--recurse-submodules",
                f"--branch={revision}",
                self.repository_url,
                str(package_dir),
            ],
            on_failure="Failed to clone the upstream source",
        )

        # Remove the Git metadata so it doesn't get packaged
        shutil.rmtree(package_dir / ".git")

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
            on_failure="Failed to compress the upstream source",
            cwd=build_dir,
        )

        # Copy the debian/ directory, if one is provided
        debian_path = self.package_root / self.name / "debian"
        if debian_path.is_dir():
            shutil.copytree(debian_path, package_dir / "debian")

        return package_dir
