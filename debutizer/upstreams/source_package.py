from pathlib import Path

from ..environment import Environment
from ..errors import UnexpectedError
from ..subprocess_utils import run
from ..version import Version
from .base import Upstream


class SourcePackageUpstream(Upstream):
    """An upstream that downloads a source package from an APT repository"""

    dsc_url: str

    def __init__(self, *, env: Environment, name: str, version: Version, dsc_url: str):
        super().__init__(env=env, name=name, version=version)
        self.dsc_url = dsc_url

    def fetch(self) -> Path:
        build_dir = self.env.build_root / self.name
        build_dir.mkdir()

        run(
            ["dget", "--quiet", self.dsc_url],
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
