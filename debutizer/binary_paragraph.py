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
        replace_if_exists: Optional[bool] = None,
        section: Optional[str] = None,
        priority: Optional[str] = None,
        essential: Optional[bool] = None,
        depends: Optional[PackageRelations] = None,
        recommends: Optional[PackageRelations] = None,
        suggests: Optional[PackageRelations] = None,
        enhances: Optional[PackageRelations] = None,
        pre_depends: Optional[PackageRelations] = None,
        homepage: Optional[str] = None,
        built_using: Optional[List[str]] = None,
        package_type: Optional[str] = None,
    ):
        super().__init__(Sources)

        self.package = package
        self.architecture = architecture
        self.description = description
        self.replace_if_exists = replace_if_exists
        self.section = section
        self.priority = priority
        self.essential = essential
        self.depends = depends
        self.recommends = recommends
        self.suggests = suggests
        self.enhances = enhances
        self.pre_depends = pre_depends
        self.homepage = homepage
        self.built_using = built_using
        self.package_type = package_type

    FIELDS = {
        "package": Field("Package"),
        "architecture": Field("Architecture"),
        "description": Field("Description"),
        "section": Field("Section"),
        "priority": Field("Priority"),
        "essential": Field("Essential"),
        "depends": Field("Depends", Field.PackageRelations()),
        "recommends": Field("Recommends", Field.PackageRelations()),
        "suggests": Field("Suggests", Field.PackageRelations()),
        "enhances": Field("Enhances", Field.PackageRelations()),
        "pre_depends": Field("Pre-Depends", Field.PackageRelations()),
        "homepage": Field("Homepage"),
        "built_using": Field("Built-Using"),
        "package_type": Field("Package-Type"),
    }
