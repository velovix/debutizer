import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Optional

from .errors import UnexpectedError
from .subprocess_utils import run
from .version import Version


@dataclass
class Upstream:
    """A way of retrieving source code and potentially package configuration from some
    source.
    """

    package_root: ClassVar[Path]
    build_root: ClassVar[Path]

    name: str
    version: Version

    def fetch(self) -> Path:
        """Retrieves data from the upstream source.

        :return: The directory with upstream source and potentially a debian/ folder
        """
        # TODO: Make this method actually abstract when MyPy supports abstract
        #       dataclasses.
        #       See: https://github.com/python/mypy/issues/5374
        raise NotImplementedError("This is an abstract method")

    def _package_dir(self) -> Path:
        return (
            self.build_root / self.name / f"{self.name}-{self.version.upstream_version}"
        )


class NullUpstream(Upstream):
    """An upstream that fetches nothing!"""

    def fetch(self) -> Path:
        self._package_dir().mkdir()
        return self._package_dir()


@dataclass
class SourceRepositoryUpstream(Upstream):
    """An upstream that clones source code from Git"""

    repository_url: str
    revision_format: str

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


@dataclass
class SourcePackageUpstream(Upstream):
    """An upstream that downloads a source package from an APT repository"""

    dsc_url: str

    def fetch(self) -> Path:
        build_dir = self.build_root / self.name
        build_dir.mkdir()

        run(
            ["dget", self.dsc_url],
            on_failure="Failed to download the source package's .dsc file",
            cwd=build_dir,
        )

        if not self._package_dir().is_dir():
            files_in_dir = list(self._package_dir().parent.iterdir())
            raise UnexpectedError(
                f"The dget command did not extract the source tarball in the expected "
                f"way. Only these files were created: {files_in_dir}."
            )

        return self._package_dir()


_SOURCES_DIR = Path("/etc/apt/sources.list.d")
