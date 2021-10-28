from pathlib import Path
from typing import List, Optional, TextIO

from debian.deb822 import Sources

from .binary_paragraph import BinaryParagraph
from .errors import CommandError
from .source_paragraph import SourceParagraph


class Control:
    source: Optional[SourceParagraph]
    binaries: List[BinaryParagraph]

    def __init__(self, package_dir: Path, package_name: str):
        self.source = None
        self.binaries = []
        self._package_name = package_name
        self._package_dir = package_dir

    @property
    def name(self) -> str:
        if self.source is None:
            raise CommandError(
                "The control object does not have a source section, so the source "
                "package name cannot be determined"
            )

        return self.source.source

    def set_source(self, source: SourceParagraph):
        self.source = source
        self.save()

    def add_binary(self, binary: BinaryParagraph, replace_if_exists: bool = False):
        for i, other in enumerate(self.binaries):
            if other.package == binary.package:
                if replace_if_exists:
                    self.binaries.pop(i)
                    break
                else:
                    raise CommandError(
                        f"A paragraph defining a binary package with the name "
                        f"'{binary.package}' already exists. It may be replaced by "
                        f"setting the replace_if_exists argument."
                    )

        self.binaries.append(binary)
        self.save()

    def save(self):
        if self.source is not None:
            control_file = self._package_dir / "debian" / "control"

            output = str(self.source.serialize())
            for binary in self.binaries:
                output += "\n\n"
                output += str(binary.serialize())

            control_file.write_text(output)

    def load(self, complete: bool):
        control_file = self._package_dir / "debian" / "control"
        if control_file.is_file():
            with control_file.open("r") as f:
                self._from_file(f)
        elif complete:
            raise CommandError(f"Package is missing a control file at {control_file}")
        else:
            self.source = None
            self.binaries = []

    def _from_file(self, file_: TextIO):
        text = file_.read()

        paragraphs = list(Sources.iter_paragraphs(text))
        if len(paragraphs) < 2:
            raise CommandError(
                "The control file must have at least two paragraphs: the source "
                "paragraph and one or more binary paragraphs"
            )

        if "Source" not in paragraphs[0]:
            raise CommandError(
                "The 'Source' field is missing from the first paragraph. The first "
                "paragraph must define a source package and contain a 'Source' field "
                "defining the source package's name."
            )
        self.source = SourceParagraph.deserialize(paragraphs[0])

        if self.source.source != self._package_name:
            raise CommandError(
                f"The Source field and package directory must have the same name. "
                f"{self.source.source} (from control file) != {self._package_name} "
                f"(from directory name)."
            )

        for i, binary in enumerate(paragraphs[1:]):
            if "Package" not in binary:
                raise CommandError(
                    f"Paragraph {i} is missing a 'Package' field. All paragraphs after "
                    f"the first paragraph must define a binary package and contain "
                    f"a 'Package' field defining the binary package's name."
                )
        self.binaries = [BinaryParagraph.deserialize(p) for p in paragraphs[1:]]
