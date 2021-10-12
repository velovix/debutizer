from typing import List, TextIO

from debian.deb822 import Sources

from .errors import CommandError


class Control:
    source: Sources
    binaries: List[Sources]

    def __init__(self):
        self.binaries = []

    @staticmethod
    def from_file(file_: TextIO):
        text = file_.read()
        control = Control()

        paragraphs = list(Sources.iter_paragraphs(text))
        if len(paragraphs) < 2:
            raise CommandError(
                "The control file must have at least two paragraphs: the source "
                "paragraph and one or more binary paragraphs"
            )

        control.source = paragraphs[0]
        if "Source" not in control.source:
            raise CommandError(
                "The 'Source' field is missing from the first paragraph. The first "
                "paragraph must define a source package and contain a 'Source' field "
                "defining the source package's name."
            )

        control.binaries = paragraphs[1:]
        for i, binary in enumerate(control.binaries):
            if "Package" not in binary:
                raise CommandError(
                    f"Paragraph {i} is missing a 'Package' field. All paragraphs after "
                    f"the first paragraph must define a binary package and contain "
                    f"a 'Package' field defining the binary package's name."
                )

    def __str__(self):
        output = str(self.source)

        for binary in self.binaries:
            output += "\n\n"
            output += str(binary)

        return output
