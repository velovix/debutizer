from pathlib import Path
from typing import Dict, List, Optional, TextIO, Union

from debian.deb822 import Sources

from .deb822_utils import ListType, add_field
from .errors import CommandError


class Control:
    source: Optional[Sources]
    binaries: List[Sources]

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

        return self.source["Source"]

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
        fields = Sources()
        add_field(fields, "Source", self._package_name)
        add_field(fields, "Maintainer", maintainer)
        add_field(fields, "Standards-Version", standards_version)

        if (vcs_type is None) != (vcs_type_value is None):
            raise CommandError(
                "Both the vcs_type and vcs_type_value args must be set together. They "
                "form a single field in the format 'Vcs-{vcs_type}: {vcs_type_value}."
            )

        if vcs_type is not None:
            add_field(fields, f"Vcs-{vcs_type}", vcs_type_value)

        add_field(fields, "Section", section)
        add_field(fields, "Priority", priority)
        add_field(fields, "Build-Depends", build_depends, ListType.COMMAS_MULTILINE)
        add_field(
            fields,
            "Build-Depends-Indep",
            build_depends_indep,
            ListType.COMMAS_MULTILINE,
        )
        add_field(
            fields, "Build-Depends-Arch", build_depends_arch, ListType.COMMAS_MULTILINE
        )
        add_field(fields, "Build-Conflicts", build_conflicts, ListType.COMMAS_MULTILINE)
        add_field(
            fields,
            "Build-Conflicts-Indep",
            build_conflicts_indep,
            ListType.COMMAS_MULTILINE,
        )
        add_field(
            fields,
            "Build-Conflicts-Arch",
            build_conflicts_arch,
            ListType.COMMAS_MULTILINE,
        )
        add_field(fields, "Homepage", homepage)
        add_field(fields, "Uploaders", uploaders)
        add_field(fields, "Vcs-Browser", vcs_browser)
        add_field(fields, "Testsuite", testsuite)
        add_field(fields, "Rules-Requires-Root", rules_requires_root)

        if others is not None:
            for name, value in others.items():
                add_field(fields, name, value)

        self.source = fields
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
        for i, binary in enumerate(self.binaries):
            if binary["Package"] == package:
                if replace_if_exists:
                    self.binaries.pop(i)
                    break
                else:
                    raise CommandError(
                        f"A paragraph defining a binary package with the name "
                        f"'{package}' already exists. It may be replaced by setting "
                        f"the replace_if_exists argument."
                    )

        fields = Sources()
        add_field(fields, "Package", package)
        add_field(fields, "Architecture", architecture)
        add_field(fields, "Description", description)

        add_field(fields, "Section", section)
        add_field(fields, "Priority", priority)
        add_field(fields, "Essential", essential)
        add_field(fields, "Depends", depends, ListType.COMMAS_MULTILINE)
        add_field(fields, "Recommends", recommends, ListType.COMMAS_MULTILINE)
        add_field(fields, "Suggests", suggests, ListType.COMMAS_MULTILINE)
        add_field(fields, "Enhances", enhances, ListType.COMMAS_MULTILINE)
        add_field(fields, "Pre-Depends", pre_depends, ListType.COMMAS_MULTILINE)
        add_field(fields, "Homepage", homepage)
        add_field(fields, "Built-Using", built_using)
        add_field(fields, "Package-Type", package_type)

        if others is not None:
            for name, value in others.items():
                add_field(fields, name, value)

        self.binaries.append(fields)
        self.save()

    def save(self):
        if self.source is not None:
            control_file = self._package_dir / "debian" / "control"

            output = str(self.source)
            for binary in self.binaries:
                output += "\n\n"
                output += str(binary)

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

        self.source = paragraphs[0]
        if "Source" not in self.source:
            raise CommandError(
                "The 'Source' field is missing from the first paragraph. The first "
                "paragraph must define a source package and contain a 'Source' field "
                "defining the source package's name."
            )

        if self.source["Source"] != self._package_name:
            raise CommandError(
                f"The Source field and package directory must have the same name. "
                f"{self.source['Source']} (from control file) != {self._package_name} "
                f"(from directory name)."
            )

        self.binaries = paragraphs[1:]
        for i, binary in enumerate(self.binaries):
            if "Package" not in binary:
                raise CommandError(
                    f"Paragraph {i} is missing a 'Package' field. All paragraphs after "
                    f"the first paragraph must define a binary package and contain "
                    f"a 'Package' field defining the binary package's name."
                )
