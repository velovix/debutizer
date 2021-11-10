from datetime import datetime
from pathlib import Path

from debutizer.binary_paragraph import BinaryParagraph
from debutizer.copyright import (
    Copyright,
    CopyrightFiles,
    CopyrightHeader,
    CopyrightLicense,
)
from debutizer.relation import PackageRelations
from debutizer.source_package import SourcePackage
from debutizer.source_paragraph import SourceParagraph
from debutizer.upstreams import LocalUpstream
from debutizer.version import Version

upstream = LocalUpstream(
    name="debutizer", version=Version.from_string("0.7.0-1"), path=Path(".")
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
                "python3-flask",
                "python3-yaml",
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
                "s3fs",
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
source_package.set_debhelper_compat_version()

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

source_package.changelog.add(
    version="0.4.4-1",
    urgency="medium",
    changes=[
        "* Add tools for editing package dependencies",
        "* Add cross-package dependency support",
        "* Allow configuration through environment variables",
    ],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 11, 4, 13, 21),
)

source_package.changelog.add(
    version="0.4.5-1",
    urgency="medium",
    changes=["* Persist changes to disk after running pre-build hooks"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 11, 4, 16, 8),
)

source_package.changelog.add(
    version="0.4.6-1",
    urgency="medium",
    changes=["* Log to stderr by default"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 11, 5, 12, 42),
)

source_package.changelog.add(
    version="0.5.0-1",
    urgency="medium",
    changes=[
        "* Fix Debutizer logs being buffered and coming in after subprocess logs",
        "* Make the Cache-Control header configurable for 's3-repo upload'",
        "* Add missing S3FS runtime dependency",
        "* Add missing pbuilder hook to APT releases",
        "* Start deploying to PyPI",
        "* Add a new 'check' subcommand for finding system packages",
    ],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 11, 5, 21, 2),
)

source_package.changelog.add(
    version="0.5.1-1",
    urgency="medium",
    changes=["* Generate S3-repo metadata using the contents of the bucket"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 11, 6, 15, 12),
)

source_package.changelog.add(
    version="0.6.0-1",
    urgency="medium",
    changes=["* Migrate some configuration to a file"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 11, 8, 23, 59),
)

source_package.changelog.add(
    version="0.7.0-1",
    urgency="medium",
    changes=["* TODO: Finish changelog"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 11, 8, 23, 59),
)

source_package.complete()
