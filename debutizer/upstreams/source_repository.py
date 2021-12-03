import shutil
from pathlib import Path
from typing import List, Union

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
        recurse_submodules: bool = True,
    ):
        """
        :param env: The current build environment
        :param name: The name of the source package this repository is for
        :param version: The version this clone corresponds to. Only the upstream version
            portion needs to be specified
        :param repository_url: The URL to the Git repository to clone
        :param revision_format: The Git tag to clone. You can add {upstream_version} to
            this string, and it will be replaced by the upstream version given by the
            "version" argument. This is commonly "v{upstream_version}". It may also be
            a commit hash or branch name.
        :param recurse_submodules: If True, the repository's submodules will be cloned
            as well
        """
        super().__init__(env=env, name=name, version=version)
        self.repository_url = repository_url
        self.revision_format = revision_format
        self.recurse_submodules = recurse_submodules

    def fetch(self) -> Path:
        revision = self.revision_format.format(
            upstream_version=self.version.upstream_version
        )

        build_dir = self.env.build_root / self.name
        build_dir.mkdir()
        package_dir = self._package_dir()

        clone_command: List[Union[str, Path]] = [
            "git",
            "clone",
            "--depth=1",
            f"--branch={revision}",
        ]

        if self.recurse_submodules:
            clone_command.append("--recurse-submodules")

        clone_command += [self.repository_url, package_dir]

        # Clone the upstream source
        run(
            clone_command,
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
