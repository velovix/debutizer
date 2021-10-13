from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from typing import List, Optional, TextIO, Union

from debian import changelog as deb_changelog

from .errors import CommandError
from .version import Version


class Changelog:
    deb_obj: Optional[deb_changelog.Changelog]

    def __init__(self, package_dir: Path, distribution: str, package_name: str):
        self.deb_obj = None
        self._package_dir = package_dir
        self._distribution = distribution
        self._package_name = package_name

    @property
    def version(self) -> str:
        if self.deb_obj is None:
            raise CommandError(
                "No changelog data has been loaded, so the current version cannot be "
                "determined"
            )
        return str(self.deb_obj.get_version())

    def save(self) -> None:
        if self.deb_obj is not None:
            changelog_file = self._package_dir / "debian" / "changelog"
            changelog_file.write_text(str(self.deb_obj))

    def load(self, complete: bool) -> None:
        changelog_file = self._package_dir / "debian" / "changelog"
        if changelog_file.is_file():
            with changelog_file.open("r") as f:
                self._from_file(f)
        elif complete:
            raise CommandError(
                f"Package is missing a changelog file at {changelog_file}"
            )
        else:
            self.deb_obj = None

    def _from_file(self, file_: TextIO) -> None:
        try:
            self.deb_obj = deb_changelog.Changelog(file_)
        except deb_changelog.ChangelogParseError as ex:
            raise CommandError(f"While parsing the changelog file: {ex}") from ex

    def add(
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
        if self.deb_obj is None:
            self.deb_obj = deb_changelog.Changelog()

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

        self.deb_obj.new_block(
            package=self._package_name,
            version=str(version),
            distributions=self._distribution,
            urgency=urgency,
            changes=changes,
            author=author,
            date=format_datetime(date),
            encoding="utf-8",
        )
        self.save()
