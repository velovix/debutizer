import shutil
from pathlib import Path

from ..commands.utils import make_source_archive
from ..environment import Environment
from ..subprocess_utils import run
from ..version import Version
from .base import Upstream


class SourceRepositoryUpstream(Upstream):
    """An upstream that clones source code from Git"""

    repository_url: str
    revision_format: str

    def __init__(
        self,
        *,
        env: Environment,
        name: str,
        version: Version,
        repository_url: str,
        revision_format: str,
    ):
        super().__init__(env=env, name=name, version=version)
        self.repository_url = repository_url
        self.revision_format = revision_format

    def fetch(self) -> Path:
        revision = self.revision_format.format(
            upstream_version=self.version.upstream_version
        )

        build_dir = self.env.build_root / self.name
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
                package_dir,
            ],
            on_failure="Failed to clone the upstream source",
        )

        # Remove the Git metadata so it doesn't get packaged
        shutil.rmtree(package_dir / ".git")

        # Create the source archive in the previous directory
        make_source_archive(
            package_dir=package_dir,
            destination_dir=build_dir,
            name=self.name,
            version=self.version,
        )

        # Copy the debian/ directory, if one is provided
        debian_path = self.env.package_root / self.name / "debian"
        if debian_path.is_dir():
            shutil.copytree(debian_path, package_dir / "debian")

        return package_dir
