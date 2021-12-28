from datetime import datetime
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

from debian import changelog as deb_changelog

from .errors import CommandError
from .version import Version


class ChangeBlock:
    def __init__(
        self,
        *,
        version: Union[str, Version],
        urgency: str,
        changes: List[str],
        author: Optional[str] = None,
        date: Optional[datetime] = None,
        package: Optional[str] = None,
        distribution: Optional[str] = None,
        urgency_comment: Optional[str] = None,
        other_pairs: Optional[Dict[str, str]] = None,
    ):
        if isinstance(version, str):
            self.version = Version.from_string(version)
        else:
            self.version = version

        self.urgency = urgency
        self.changes = changes
        self.author = author
        self.date = date
        self.package = package
        self.distribution = distribution
        self.urgency_comment = urgency_comment
        self.other_pairs = other_pairs

    def serialize(self) -> deb_changelog.ChangeBlock:
        return deb_changelog.ChangeBlock(
            package=self.package,
            version=str(self.version),
            distributions=self.distribution,
            urgency=self.urgency,
            urgency_comment=self.urgency_comment,
            changes=self._format_changes(),
            author=self.author,
            date=self._format_datetime(),
            other_pairs=self.other_pairs,
        )

    @classmethod
    def deserialize(cls, deb_block: deb_changelog.ChangeBlock) -> "ChangeBlock":
        return ChangeBlock(
            version=str(deb_block.version),
            urgency=deb_block.urgency,
            changes=cls._unformat_changes(deb_block.changes()),
            author=deb_block.author,
            date=cls._unformat_date(deb_block.date),
            package=deb_block.package,
            distribution=deb_block.distributions,
            urgency_comment=deb_block.urgency_comment,
            other_pairs=deb_block.other_pairs,
        )

    def _format_changes(self) -> List[str]:
        """Converts the changes list into the indented, padded format expected by
        debian-python
        """
        formatted = []

        # Give each change indentation
        for change in self.changes:
            if len(change) > 0:
                formatted.append(f"  {change}")
            else:
                # Empty lines don't traditionally have indentation
                formatted.append(change)

        # The changes list must start and end with empty strings, unfortunately
        formatted = [""] + formatted + [""]

        return formatted

    @classmethod
    def _unformat_changes(cls, deb_changes: List[str]) -> List[str]:
        """Converts the changes list into a more usable unindented, un-padded format"""
        output = []

        # Remove the top and bottom padding lines
        if len(deb_changes) > 0:
            if deb_changes[0].strip() == "":
                deb_changes.pop(0)
            if deb_changes[-1].strip() == "":
                deb_changes.pop(-1)

        for change in deb_changes:
            # TODO: Are changelog files allowed to have differently sized indentation?
            output.append(change[2:])

        return output

    def _format_datetime(self) -> Optional[str]:
        """Converts the datetime into an RFC 2822 formatted string expected by
        debian-python
        """
        if self.date is None:
            return None
        return format_datetime(self.date)

    @classmethod
    def _unformat_date(cls, date: Optional[str]) -> Optional[datetime]:
        """Converts an RFC 2822 formatted string to a datetime"""
        if date is None:
            return date
        return parsedate_to_datetime(date)


class Changelog:
    def __init__(self, package_dir: Path, distribution: str, package: str):
        self._package_dir = package_dir
        self._distribution = distribution
        self._package = package

        self.blocks: List[ChangeBlock] = []

    @property
    def version(self) -> str:
        if len(self.blocks) == 0:
            raise CommandError(
                "No changelog data has been loaded, so the current version cannot be "
                "determined"
            )
        return str(self.blocks[0].version)

    def save(self) -> None:
        if len(self.blocks) == 0:
            return

        deb_obj = deb_changelog.Changelog()

        # The block order must be reversed because `new_block` appends entries
        # to the top of the changelog, not the bottom
        for block in reversed(self.blocks):
            deb_block = block.serialize()
            deb_obj.new_block(
                package=deb_block.package,
                version=deb_block.version,
                distributions=deb_block.distributions,
                urgency=deb_block.urgency,
                urgency_comment=deb_block.urgency_comment,
                changes=deb_block.changes(),
                author=deb_block.author,
                date=deb_block.date,
                other_pairs=deb_block.other_pairs,
                encoding="utf-8",
            )

        changelog_file = self._package_dir / self.FILE_PATH
        changelog_file.write_text(str(deb_obj))

    def load(self) -> None:
        changelog_file = self._package_dir / self.FILE_PATH
        if changelog_file.is_file():
            with changelog_file.open("r") as f:
                self._from_file(f)

    def _from_file(self, file_: TextIO) -> None:
        try:
            deb_obj = deb_changelog.Changelog(file_)
        except deb_changelog.ChangelogParseError as ex:
            raise CommandError(f"While parsing the changelog file: {ex}") from ex

        for deb_block in deb_obj:
            block = ChangeBlock.deserialize(deb_block)
            self.blocks.append(block)

    def add(self, block: ChangeBlock) -> None:
        """Adds an entry to the top of the changelog"""
        if len(block.changes) == 0:
            raise CommandError("A new changelog block must have at least one change")

        if block.distribution is None:
            block.distribution = self._distribution
        if block.package is None:
            block.package = self._package

        self.blocks.insert(0, block)

    FILE_PATH = Path("debian/changelog")
