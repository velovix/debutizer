from datetime import datetime
from pathlib import Path

from debutizer.binary_paragraph import BinaryParagraph
from debutizer.copyright import (
    Copyright,
    CopyrightFiles,
    CopyrightHeader,
    CopyrightLicense,
)
from debutizer.relation import Dependency, PackageRelations, Relation
from debutizer.source_package import SourcePackage
from debutizer.source_paragraph import SourceParagraph
from debutizer.upstreams import LocalUpstream
from debutizer.version import Version

upstream = LocalUpstream(
    name="debutizer", version=Version.from_string("0.3.0-1"), path=Path(".")
)
package_dir = upstream.fetch()

source_package = SourcePackage(package_dir, complete=False)

source_package.set_source_format()

source_package.control.set_source(
    SourceParagraph(
        source=source_package.name,
        maintainer="Tyler Compton <xaviosx@gmail.com>",
        section="utils",
        priority="optional",
        build_depends=PackageRelations.from_strings(
            [
                "debhelper",
                "dh-python",
                "python3-all",
                "python3-pytest",
                "python3-setuptools",
                "python3-debian",
                "python3-xdg",
                "python3-requests",
                "s3fs",
            ]
        ),
        uploaders=["Tyler Compton <xaviosx@gmail.com>"],
        homepage="https://github.com/velovix/debutizer",
    )
)
source_package.control.add_binary(
    BinaryParagraph(
        package="debutizer",
        architecture="any",
        description="A tool for managing APT packages",
        section="utils",
        priority="optional",
        depends=PackageRelations.from_strings(
            [
                "${python3:Depends}",
                "${misc:Depends}",
                "pbuilder",
                "devscripts",
                "quilt",
            ]
        ),
        recommends=PackageRelations.from_strings(
            [
                "debian-keyring",
            ]
        ),
        homepage="https://github.com/velovix/debutizer",
    )
)

source_package.copyright.set_header(
    CopyrightHeader(
        upstream_name="debutizer",
        upstream_contact=["Tyler Compton <xaviosx@gmail.com>"],
        source="https://github.com/velovix/debutizer",
        license_="BSD-3-Clause",
        copyright_="Copyright 2021 Tyler Compton",
    )
)
source_package.copyright.add_files(
    CopyrightFiles(
        files=["*", "debian/*"],
        copyright_="Copyright 2021 Tyler Compton",
        license_="BSD-3-Clause",
    )
)
source_package.copyright.add_license(
    CopyrightLicense(
        license_=Copyright.full_license_text("BSD-3-Clause"),
    )
)
source_package.compat.from_distribution()

source_package.changelog.add(
    version="0.2.0-1",
    urgency="medium",
    changes=["* Initial packaging"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 10, 11, 22, 46),
)

source_package.changelog.add(
    version="0.3.0-1",
    urgency="medium",
    changes=["* Add support for GPG signing"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 10, 25, 22, 58),
)

source_package.complete()
