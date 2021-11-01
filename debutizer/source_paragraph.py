from typing import List, Optional

from debian.deb822 import Sources

from .deb822_schema import Deb822Schema, T
from .deb822_utils import Field
from .relation import PackageRelations


class SourceParagraph(Deb822Schema):
    """Data from the first paragraph in the control file defining the source
    paragraph
    """

    def __init__(
        self,
        *,
        source: str,
        maintainer: str,
        standards_version: str = "4.5.0",
        section: Optional[str] = None,
        priority: Optional[str] = None,
        build_depends: Optional[PackageRelations] = None,
        build_depends_indep: Optional[PackageRelations] = None,
        build_depends_arch: Optional[PackageRelations] = None,
        build_conflicts: Optional[PackageRelations] = None,
        build_conflicts_indep: Optional[PackageRelations] = None,
        build_conflicts_arch: Optional[PackageRelations] = None,
        uploaders: Optional[List[str]] = None,
        homepage: Optional[str] = None,
        vcs_type: Optional[str] = None,
        vcs_type_value: Optional[str] = None,
        vcs_browser: Optional[str] = None,
        testsuite: List[str] = None,
        rules_requires_root: Optional[str] = None,
    ):
        super().__init__(Sources)

        self.source = source
        self.maintainer = maintainer
        self.standards_version = standards_version
        self.section = section
        self.priority = priority
        self.build_depends = build_depends
        self.build_depends_indep = build_depends_indep
        self.build_depends_arch = build_depends_arch
        self.build_conflicts = build_conflicts
        self.build_conflicts_indep = build_conflicts_indep
        self.build_conflicts_arch = build_conflicts_arch
        self.uploaders = uploaders
        self.homepage = homepage
        self.vcs_type = vcs_type
        self.vcs_type_value = vcs_type_value
        self.vcs_browser = vcs_browser
        self.testsuite = testsuite
        self.rules_requires_root = rules_requires_root

    def serialize(self) -> T:
        deb822: T = super().serialize()

        if self.vcs_type is not None and self.vcs_type_value is not None:
            deb822[f"Vcs-{self.vcs_type}"] = self.vcs_type_value

        return deb822

    @classmethod
    def deserialize(cls, deb822: T) -> "SourceParagraph":
        inputs = cls._deserialize_fields(deb822)

        vcs_type = None
        vcs_type_value = None
        for key in deb822:
            if key.lower().startswith("vcs-") and key.lower() != "vcs-browser":
                vcs_type_value = deb822[key]
                vcs_type = key.split("-")[1]

        return SourceParagraph(
            **inputs,
            vcs_type=vcs_type,
            vcs_type_value=vcs_type_value,
        )

    def all_build_depends(self) -> PackageRelations:
        all_relations = PackageRelations([])

        if self.build_depends is not None:
            for relation in self.build_depends:
                all_relations.add_relation(relation, replace=True)
        if self.build_depends_indep:
            for relation in self.build_depends_indep:
                all_relations.add_relation(relation, replace=True)
        if self.build_depends_arch:
            for relation in self.build_depends_arch:
                all_relations.add_relation(relation, replace=True)

        return all_relations

    FIELDS = {
        "source": Field("Source"),
        "maintainer": Field("Maintainer"),
        "standards_version": Field("Standards-Version"),
        "section": Field("Section"),
        "priority": Field("Priority"),
        "build_depends": Field("Build-Depends", Field.PackageRelations()),
        "build_depends_indep": Field("Build-Depends-Indep", Field.PackageRelations()),
        "build_depends_arch": Field("Build-Depends-Arch", Field.PackageRelations()),
        "build_conflicts": Field("Build-Conflicts", Field.PackageRelations()),
        "build_conflicts_indep": Field(
            "Build-Conflicts-Indep", Field.PackageRelations()
        ),
        "build_conflicts_arch": Field("Build-Conflicts-Arch", Field.PackageRelations()),
        "uploaders": Field("Uploaders", Field.Array(Field.Array.Separator.COMMAS)),
        "homepage": Field("Homepage"),
        "vcs_browser": Field("Vcs-Browser"),
        "testsuite": Field("Testsuite"),
        "rules_requires_root": Field("Rules-Requires-Root"),
    }
