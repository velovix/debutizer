from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

from debian import copyright as deb_copyright
from debian.deb822 import Deb822

from ._license_full_text import spdx_to_full_text
from .deb822_utils import ListType, add_field
from .errors import CommandError

_COPYRIGHT_FORMAT = "https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"


class Copyright:
    deb_obj: Optional[deb_copyright.Copyright]

    def __init__(self, package_dir: Path):
        self.deb_obj = None
        self._package_dir = package_dir

    def save(self):
        if self.deb_obj is not None:
            copyright_file = self._package_dir / "debian" / "copyright"
            copyright_file.write_text(self.deb_obj.dump())

    def load(self, complete: bool):
        copyright_file = self._package_dir / "debian" / "copyright"
        if copyright_file.is_file():
            with copyright_file.open("r") as f:
                self._from_file(f)
        elif complete:
            raise CommandError(
                f"Package is missing a copyright file at {copyright_file}"
            )
        else:
            self.deb_obj = None

    def _from_file(self, file_: TextIO):
        try:
            self.deb_obj = deb_copyright.Copyright(file_)
        except deb_copyright.NotMachineReadableError as ex:
            raise CommandError(f"While parsing the copyright file: {ex}") from ex

    def set_header(
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
        if self.deb_obj is None:
            self.deb_obj = deb_copyright.Copyright()

        fields = Deb822()

        add_field(fields, "Format", format_)
        add_field(fields, "Upstream-Name", upstream_name)
        add_field(fields, "Upstream-Contact", upstream_contact, ListType.LINE_BASED)
        add_field(fields, "Source", source)
        add_field(fields, "Disclaimer", disclaimer)
        add_field(fields, "Comment", comment)
        add_field(fields, "License", license_)  # TODO: Manage indentation. Synopsis?
        add_field(fields, "Copyright", copyright_)  # TODO: No synopsis?

        if others is not None:
            for name, value in others.items():
                add_field(fields, name, value)

        self.deb_obj.header = deb_copyright.Header(data=fields)

        self.save()

    def add_files(
        self,
        *,
        files: List[str],
        copyright_: str,
        license_: str,
        comment: Optional[str] = None,
    ):
        if self.deb_obj is None:
            self.deb_obj = deb_copyright.Copyright()

        fields = Deb822()

        add_field(fields, "Files", files, ListType.WHITESPACE_SEPARATED)
        add_field(fields, "Copyright", copyright_)  # TODO: No synopsis?
        add_field(fields, "License", license_)  # TODO: Synopsis?
        if comment is not None:
            add_field(fields, "Comment", comment)  # TODO: No synopsis?

        self.deb_obj.add_files_paragraph(deb_copyright.FilesParagraph(data=fields))

        self.save()

    def add_license(self, *, license_: str, comment: Optional[str] = None):
        if self.deb_obj is None:
            self.deb_obj = deb_copyright.Copyright()

        fields = Deb822()

        add_field(fields, "License", license_)  # TODO: Synopsis?
        if comment is not None:
            add_field(fields, "Comment", comment)  # TODO: No synopsis?

        self.deb_obj.add_license_paragraph(deb_copyright.LicenseParagraph(data=fields))

    @staticmethod
    def full_license_text(spdx_identifier: str) -> str:
        """
        :param spdx_identifier: The SPDX identifier of the desired license
        :return: The full license text, including the identifier as the synopsis
        """
        if spdx_identifier not in spdx_to_full_text:
            raise CommandError(
                f"No full license text for SPDX identifier '{spdx_identifier}'. "
                f"Supported licenses are: {spdx_to_full_text.keys()}."
            )

        full_text = spdx_to_full_text[spdx_identifier]
        full_text_formatted = ""
        for line in full_text.split("\n"):
            # Empty lines are not allowed, probably to simplify parsing for Debian tools
            if line.strip() == "":
                line = "."

            # License are always going to be multi-line strings, so they must have
            # indentation to show that they are a continuation of the same field
            line = f" {line}"
            full_text_formatted += f"{line}\n"

        # Trailing newlines are not allowed
        if full_text_formatted.endswith("\n"):
            full_text_formatted = full_text_formatted[:-1]

        return f"{spdx_identifier}\n{full_text_formatted}"
