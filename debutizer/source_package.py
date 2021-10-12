from datetime import datetime
from email.utils import format_datetime
from enum import Enum
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Union

from debian.changelog import Changelog
from debian.copyright import Copyright, Header
from debian.deb822 import Sources

from .control import Control
from .errors import CommandError, UnexpectedError
from .subprocess_utils import run
from .version import Version

_COPYRIGHT_FORMAT = "https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"


class SourcePackage:
    """A Python representation of a source package definition"""

    distribution: ClassVar[Optional[str]] = None

    changelog: Optional[Changelog]
    control: Optional[Control]
    copyright: Optional[Copyright]
    package_dir: Path
    _complete: bool

    def __init__(self, package_dir: Path, complete: bool = True):
        """Creates a SourcePackage configured using files found in the given directory.

        :param package_dir: The package directory, as created by an upstream
        :param complete: If True, configuration in the package directory is expected
            to be finished and static checks will be performed against it
        """
        self.package_dir = package_dir
        self._complete = complete
        self.load()

    @property
    def name(self) -> str:
        """
        :return: The name of the source package
        """
        if self.control is None:
            raise CommandError(
                "No control data has been loaded, so the source package name cannot be "
                "determined"
            )
        return self.control.source["Source"]

    @property
    def version(self) -> str:
        """
        :return: The current version of the source package
        """
        if self.changelog is None:
            raise CommandError(
                "No changelog data has been loaded, so the current version cannot be "
                "determined"
            )
        return str(self.changelog.get_version())

    def save(self) -> None:
        """Persists any changes made to this object to the disk"""
        if self.changelog is not None:
            changelog_file = self.package_dir / "debian" / "changelog"
            changelog_file.write_text(str(self.changelog))

        if self.control is not None:
            control_file = self.package_dir / "debian" / "control"
            control_file.write_text(str(self.control))

        if self.copyright is not None:
            copyright_file = self.package_dir / "debian" / "copyright"
            copyright_file.write_text(str(self.copyright))

    def load(self) -> None:
        """Applies changes from the disk to this object"""
        changelog_file = self.package_dir / "debian" / "changelog"
        if changelog_file.is_file():
            with changelog_file.open("r") as f:
                self.changelog = Changelog(f)
        elif self._complete:
            raise CommandError(
                f"Package is missing a changelog file at {changelog_file}"
            )
        else:
            self.changelog = None

        control_file = self.package_dir / "debian" / "control"
        if changelog_file.is_file():
            with control_file.open("r") as f:
                self.control = Control.from_file(f)
        elif self._complete:
            raise CommandError(f"Package is missing a control file at {control_file}")
        else:
            self.control = None

        copyright_file = self.package_dir / "debian" / "copyright"
        if copyright_file.is_file():
            with copyright_file.open("r") as f:
                self.copyright = Copyright(f)
        elif self._complete:
            raise CommandError(
                f"Package is missing a copyright file at {copyright_file}"
            )
        else:
            self.copyright = None

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

    def add_to_changelog(
        self,
        *,
        version: Union[str, Version],
        urgency: str,
        changes: List[str],
        author: str,
        date: datetime,
    ):
        """Adds an entry to the top of the changelog. This is a small wrapper around
        Changelog.new_block, filling in some fields automatically and excluding unused
        ones, then persists the changes to the disk. Unlike Changelog.new_block, this
        method will handle formatting, including indentation, automatically.

        :param version: The new version introduced by these changes
        :param urgency: The urgency to update
        :param changes: A description of each new change
        :param author: The author of these changes
        :param date: The date of the changes
        """
        if self.distribution is None:
            raise UnexpectedError("The distribution field must be set!")

        if self.changelog is None:
            self.changelog = Changelog()

        # Ensure that the version is properly formatted
        if isinstance(version, str):
            version = Version.from_string(version)

        if len(changes) == 0:
            raise CommandError("A new changelog block must have at least one change")

        # Give each change indentation
        for i, change in enumerate(changes):
            changes[i] = f"  {change}"
        # Attempt to properly format the given change list
        # The changes list must start and end with empty strings, unfortunately
        changes = [""] + changes + [""]

        self.changelog.new_block(
            package=self.name,
            version=str(version),
            distributions=self.distribution,
            urgency=urgency,
            changes=changes,
            author=author,
            date=format_datetime(date),
            encoding="utf-8",
        )
        self.save()

    def set_source_package(
        self,
        *,
        maintainer: str,
        standards_version: str = "4.5.0",
        section: Optional[str] = None,
        priority: Optional[str] = None,
        build_depends: Optional[List[str]] = None,
        build_depends_indep: Optional[List[str]] = None,
        build_depends_arch: Optional[List[str]] = None,
        build_conflicts: Optional[List[str]] = None,
        build_conflicts_indep: Optional[List[str]] = None,
        build_conflicts_arch: Optional[List[str]] = None,
        uploaders: Optional[List[str]] = None,
        homepage: Optional[str] = None,
        vcs_type: Optional[str] = None,
        vcs_type_value: Optional[str] = None,
        vcs_browser: Optional[str] = None,
        testsuite: List[str] = None,
        rules_requires_root: Optional[str] = None,
        others: Dict[str, Union[str, List[str]]] = None,
    ):
        if self.control is None:
            self.control = Control()

        fields: List[str] = []
        _add_field(fields, "Source", self.name)
        _add_field(fields, "Maintainer", maintainer)
        _add_field(fields, "Standards-Version", standards_version)

        if (vcs_type is None) != (vcs_type_value is None):
            raise CommandError(
                "Both the vcs_type and vcs_type_value args must be set together. They "
                "form a single field in the format 'Vcs-{vcs_type}: {vcs_type_value}."
            )

        if vcs_type is not None:
            _add_field(fields, f"Vcs-{vcs_type}", vcs_type_value)

        _add_field(fields, "Section", section)
        _add_field(fields, "Priority", priority)
        _add_field(fields, "Build-Depends", build_depends, ListType.COMMAS_MULTILINE)
        _add_field(
            fields,
            "Build-Depends-Indep",
            build_depends_indep,
            ListType.COMMAS_MULTILINE,
        )
        _add_field(
            fields, "Build-Depends-Arch", build_depends_arch, ListType.COMMAS_MULTILINE
        )
        _add_field(
            fields, "Build-Conflicts", build_conflicts, ListType.COMMAS_MULTILINE
        )
        _add_field(
            fields,
            "Build-Conflicts-Indep",
            build_conflicts_indep,
            ListType.COMMAS_MULTILINE,
        )
        _add_field(
            fields,
            "Build-Conflicts-Arch",
            build_conflicts_arch,
            ListType.COMMAS_MULTILINE,
        )
        _add_field(fields, "Homepage", homepage)
        _add_field(fields, "Uploaders", uploaders)
        _add_field(fields, "Vcs-Browser", vcs_browser)
        _add_field(fields, "Testsuite", testsuite)
        _add_field(fields, "Rules-Requires-Root", rules_requires_root)

        if others is not None:
            for name, value in others.items():
                _add_field(fields, name, value)

        self.control.source = Sources(fields=fields)
        self.save()

    def add_binary_package(
        self,
        *,
        package: str,
        architecture: str,
        description: str,
        replace_if_exists: bool = False,
        section: Optional[str] = None,
        priority: Optional[str] = None,
        essential: Optional[bool] = None,
        depends: Optional[List[str]] = None,
        recommends: Optional[List[str]] = None,
        suggests: Optional[List[str]] = None,
        enhances: Optional[List[str]] = None,
        pre_depends: Optional[List[str]] = None,
        homepage: Optional[str] = None,
        built_using: Optional[List[str]] = None,
        package_type: Optional[str] = None,
        others: Dict[str, Union[str, List[str]]] = None,
    ):
        if self.control is None:
            self.control = Control()

        for i, binary in enumerate(self.control.binaries):
            if binary["Package"] == package:
                if replace_if_exists:
                    self.control.binaries.pop(i)
                    break
                else:
                    raise CommandError(
                        f"A paragraph defining a binary package with the name "
                        f"'{package}' already exists. It may be replaced by setting "
                        f"the replace_if_exists argument."
                    )

        fields: List[str] = []
        _add_field(fields, "Package", package)
        _add_field(fields, "Architecture", architecture)
        _add_field(fields, "Description", description)

        _add_field(fields, "Section", section)
        _add_field(fields, "Priority", priority)
        _add_field(fields, "Essential", essential)
        _add_field(fields, "Depends", depends, ListType.COMMAS_MULTILINE)
        _add_field(fields, "Recommends", recommends, ListType.COMMAS_MULTILINE)
        _add_field(fields, "Suggests", suggests, ListType.COMMAS_MULTILINE)
        _add_field(fields, "Enhances", enhances, ListType.COMMAS_MULTILINE)
        _add_field(fields, "Pre-Depends", pre_depends, ListType.COMMAS_MULTILINE)
        _add_field(fields, "Homepage", homepage)
        _add_field(fields, "Built-Using", built_using)
        _add_field(fields, "Package-Type", package_type)

        if others is not None:
            for name, value in others.items():
                _add_field(fields, name, value)

        self.control.binaries.append(Sources(fields=fields))
        self.save()

    def set_copyright_header(
        self,
        *,
        format_: str = _COPYRIGHT_FORMAT,
        upstream_name: Optional[str] = None,
        upstream_contact: Optional[List[str]] = None,
        source: Optional[str] = None,
        disclaimer: Optional[str] = None,
        comment: Optional[str] = None,
        license_: Optional[str] = None,
        copyright_: Optional[str] = None,
        others: Dict[str, Union[str, List[str]]] = None,
    ):
        if self.copyright is None:
            self.copyright = Copyright()

        fields: List[str] = []

        _add_field(fields, "Format", format_)
        _add_field(fields, "Upstream-Name", upstream_name)
        _add_field(fields, "Upstream-Contact", upstream_contact, ListType.LINE_BASED)
        _add_field(fields, "Source", source)
        _add_field(fields, "Disclaimer", disclaimer)
        _add_field(fields, "Comment", comment)
        _add_field(fields, "License", license_)  # TODO: Manage indentation. Synopsis?
        _add_field(fields, "Copyright", copyright_)  # TODO: No synopsis?

        if others is not None:
            for name, value in others.items():
                _add_field(fields, name, value)

        self.save()


class ListType(Enum):
    """Debian files have a few ways of defining lists"""

    COMMAS = 1
    """A single line, with commas between elements"""
    COMMAS_MULTILINE = 2
    """A line per element, with a comma between elements. Usually (always?)
    syntactically the same as COMMAS, but looks better for long lists.
    """
    WHITESPACE_SEPARATED = 3
    """A single line, with spaces between elements"""
    LINE_BASED = 4
    """A line per element, with no other separator"""


def _add_field(
    fields: List[str],
    name: str,
    value: Optional[Union[str, List[str], bool]],
    list_type: ListType = ListType.COMMAS,
):
    if value is None:
        return

    if isinstance(value, str):
        value_str = value
    elif isinstance(value, list):
        if list_type is ListType.COMMAS:
            value_str = ", ".join(value)
        elif list_type is ListType.COMMAS_MULTILINE:
            value_str = ""
            for item in value:
                value_str += f"\n {item},"
        elif list_type is ListType.WHITESPACE_SEPARATED:
            value_str = " ".join(value)
        elif list_type is ListType.LINE_BASED:
            value_str = ""
            for item in value:
                value_str += f"\n {item}"
        else:
            raise UnexpectedError(f"Unknown ListType '{list_type}'.")
    elif isinstance(value, bool):
        value_str = "yes" if value else "no"
    else:
        raise CommandError(f"Invalid value type for field '{name}': {type(value)}")

    fields.append(f"{name}: {value_str}")
