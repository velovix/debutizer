from pathlib import Path
from typing import ClassVar, Optional

from .changelog import Changelog
from .control import Control
from .copyright import Copyright
from .errors import CommandError, UnexpectedError
from .subprocess_utils import run


class SourcePackage:
    """A Python representation of a source package definition"""

    distribution: ClassVar[Optional[str]] = None

    changelog: Changelog
    control: Control
    copyright: Copyright
    package_dir: Path
    _complete: bool

    def __init__(self, package_dir: Path, complete: bool = True):
        """Creates a SourcePackage configured using files found in the given directory.

        :param package_dir: The package directory, as created by an upstream
        :param complete: If True, configuration in the package directory is expected
            to be finished and static checks will be performed against it
        """
        if self.distribution is None:
            raise UnexpectedError("The distribution field must be set!")

        self.package_dir = package_dir
        self.changelog = Changelog(package_dir, self.distribution, self.name)
        self.control = Control(package_dir, self.name)
        self.copyright = Copyright(package_dir)
        self._complete = complete
        self.load()

    @property
    def name(self) -> str:
        """
        :return: The name of the source package
        """
        return self.package_dir.parent.name

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

    def load(self) -> None:
        """Applies changes from the disk to this object"""
        self.copyright.load(self._complete)
        self.control.load(self._complete)
        self.copyright.load(self._complete)

    def complete(self):
        """Mark the SourcePackage as complete, which will load the latest from the disk
        and do static checks.
        """
        self._complete = True
        self.save()
        self.load()

    def set_source_format(self, format_: str = "3.0 (quilt)") -> None:
        source_format_file = self.package_dir / "debian" / "source" / "format"
        source_format_file.parent.mkdir(parents=True, exist_ok=True)
        source_format_file.write_text(format_)

    def apply_patches(self) -> None:
        """Applies Quilt patch files found in the patches/ directory"""
        patches_dir = self.package_dir / "patches"
        if not patches_dir.is_dir():
            raise CommandError("The package has no patches directory")

        run(
            ["quilt", "push", "-a"],
            on_failure="Failed to apply patches",
            cwd=self.package_dir,
            env={
                "QUILT_PATCHES": str(self.package_dir / "patches"),
            },
        )

        self.load()
