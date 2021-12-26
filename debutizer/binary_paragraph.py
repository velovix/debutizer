from typing import List, Optional

from debian.deb822 import Sources

from debutizer.deb822_schema import Deb822Schema
from debutizer.deb822_utils import Field
from debutizer.relation import PackageRelations


class BinaryParagraph(Deb822Schema):
    """Data from paragraphs in the control file defining binary packages"""

    def __init__(
        self,
        *,
        package: str,
        architecture: str,
        description: str,
        build_profiles: Optional[str] = None,
        protected: Optional[bool] = None,
        replace_if_exists: Optional[bool] = None,
        section: Optional[str] = None,
        priority: Optional[str] = None,
        essential: Optional[bool] = None,
        build_essential: Optional[bool] = None,
        multi_arch: Optional[str] = None,
        tag: Optional[List[str]] = None,
        depends: Optional[PackageRelations] = None,
        recommends: Optional[PackageRelations] = None,
        suggests: Optional[PackageRelations] = None,
        enhances: Optional[PackageRelations] = None,
        conflicts: Optional[PackageRelations] = None,
        pre_depends: Optional[PackageRelations] = None,
        breaks: Optional[PackageRelations] = None,
        replaces: Optional[PackageRelations] = None,
        provides: Optional[PackageRelations] = None,
        homepage: Optional[str] = None,
        built_using: Optional[List[str]] = None,
        subarchitecture: Optional[str] = None,
        kernel_version: Optional[str] = None,
        installer_menu_item: Optional[str] = None,
        package_type: Optional[str] = None,
    ):
        super().__init__(Sources)

        self.package = package
        self.architecture = architecture
        self.description = description
        self.build_profiles = build_profiles
        self.protected = protected
        self.replace_if_exists = replace_if_exists
        self.section = section
        self.priority = priority
        self.essential = essential
        self.build_essential = build_essential
        self.multi_arch = multi_arch
        self.tag = tag
        self.depends = depends
        self.recommends = recommends
        self.suggests = suggests
        self.enhances = enhances
        self.conflicts = conflicts
        self.pre_depends = pre_depends
        self.breaks = breaks
        self.replaces = replaces
        self.provides = provides
        self.homepage = homepage
        self.built_using = built_using
        self.subarchitecture = subarchitecture
        self.kernel_version = kernel_version
        self.installer_menu_item = installer_menu_item
        self.package_type = package_type

    FIELDS = {
        "package": Field("Package"),
        "architecture": Field("Architecture"),
        "description": Field("Description"),
        "build_profiles": Field("Build-Profiles"),
        "protected": Field("Protected"),
        "section": Field("Section"),
        "priority": Field("Priority"),
        "essential": Field("Essential"),
        "build_essential": Field("Build-Essential"),
        "multi_arch": Field("Multi-Arch"),
        "tag": Field("Tag", Field.Array(Field.Array.Separator.WHITESPACE_SEPARATED)),
        "depends": Field("Depends", Field.PackageRelations()),
        "recommends": Field("Recommends", Field.PackageRelations()),
        "suggests": Field("Suggests", Field.PackageRelations()),
        "enhances": Field("Enhances", Field.PackageRelations()),
        "conflicts": Field("conflicts", Field.PackageRelations()),
        "pre_depends": Field("Pre-Depends", Field.PackageRelations()),
        "breaks": Field("Breaks", Field.PackageRelations()),
        "replaces": Field("Replaces", Field.PackageRelations()),
        "provides": Field("Provides", Field.PackageRelations()),
        "homepage": Field("Homepage"),
        "built_using": Field("Built-Using"),
        "subarchitecture": Field("Subarchitecture"),
        "kernel_version": Field("Kernel-Version"),
        "installer_menu_item": Field("Installer-Menu-Item"),
        "package_type": Field("Package-Type"),
    }
