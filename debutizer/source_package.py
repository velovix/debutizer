from pathlib import Path
from typing import Optional

from .changelog import Changelog
from .compat import Compat
from .conffiles import ConfFiles
from .control import Control
from .copyright import Copyright
from .environment import Environment
from .errors import CommandError
from .relation import Relation
from .subprocess_utils import run


class SourcePackage:
    """A Python representation of a source package definition"""

    changelog: Changelog
    control: Control
    copyright: Copyright
    directory: Path
    compat: Compat

    def __init__(self, env: Environment, directory: Path):
        """Creates a SourcePackage configured using files found in the given directory.

        :param directory: The directory containing the upstream source and debian/
            folder
        """
        self._env = env

        self.directory = directory
        self.changelog = Changelog(directory, env.codename, self.name)
        self.control = Control(directory, self.name)
        self.copyright = Copyright(directory)
        self.compat = Compat(directory)
        self.source_format: Optional[str] = None
        self.conffiles = ConfFiles(directory)
        self.load()

    @property
    def name(self) -> str:
        """
        :return: The name of the source package
        """
        return self.directory.parent.name

    @property
    def version(self) -> str:
        """
        :return: The current version of the source package
        """
        return self.changelog.version

    def save(self) -> None:
        """Persists any changes made to this object to the disk"""
        self.changelog.save()
        self.control.save()
        self.copyright.save()
        self.compat.save()
        self.conffiles.save()

        if self.source_format is not None:
            source_format_file = self.directory / self._SOURCE_FORMAT_PATH
            source_format_file.parent.mkdir(parents=True, exist_ok=True)
            source_format_file.write_text(self.source_format)

    def load(self) -> None:
        """Applies changes from the disk to this object"""
        self.copyright.load()
        self.control.load()
        self.copyright.load()
        self.compat.load()
        self.conffiles.load()

        source_format_file = self.directory / self._SOURCE_FORMAT_PATH
        if source_format_file.is_file():
            self.source_format = source_format_file.read_text().strip()

    def apply_patches(self) -> None:
        """Applies Quilt patch files found in the patches/ directory"""
        patches_dir = self.directory / "patches"
        if not patches_dir.is_dir():
            raise CommandError("The package has no patches directory")

        run(
            ["quilt", "push", "-a"],
            on_failure="Failed to apply patches",
            cwd=self.directory,
            env={
                "QUILT_PATCHES": str(self.directory / "patches"),
            },
        )

        self.load()

    def set_debhelper_compat_version(self, version: Optional[str] = None) -> None:
        """Sets the debhelper compatibility version. This replaces any existing
        compatibility versions, be they specified in a compat file or as a build
        dependency.

        :param version: The compat version. If None, the compatibility version is
            automatically selected based on the current distribution
        """
        if version is None:
            version = self._env.compat_version()

        set_in_build_depends = False
        if (
            self.control.source is not None
            and self.control.source.build_depends is not None
        ):
            for relation in self.control.source.build_depends.parsed():
                for dependency in relation:
                    if (
                        dependency.name == "debhelper-compat"
                        and dependency.version is not None
                    ):
                        set_in_build_depends = True

        if set_in_build_depends:
            # We know that source and build_depends are not None from the previous check
            self.control.source.build_depends.add_relation(  # type: ignore[union-attr]
                Relation.from_string(f"debhelper-compat (= {version})"),
                replace=True,
            )
        else:
            self.compat.version = version

    def __repr__(self) -> str:
        return f"SourcePackage(name={self.name}, version={self.version})"

    _SOURCE_FORMAT_PATH = Path("debian/source/format")
