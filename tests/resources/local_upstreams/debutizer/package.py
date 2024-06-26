from datetime import datetime
from pathlib import Path

from debutizer.binary_paragraph import BinaryParagraph
from debutizer.changelog import ChangeBlock
from debutizer.copyright import (
    Copyright,
    CopyrightFiles,
    CopyrightHeader,
    CopyrightLicense,
)
from debutizer.environment import Environment
from debutizer.relation import PackageRelations
from debutizer.source_package import SourcePackage
from debutizer.source_paragraph import SourceParagraph
from debutizer.upstreams import LocalUpstream
from debutizer.version import Version


def create_source_package(env: Environment) -> SourcePackage:
    upstream = LocalUpstream(
        env=env, name="debutizer", version=Version.from_string("0.14.0"), path=Path(".")
    )
    package_dir = upstream.fetch()

    source_package = SourcePackage(env, package_dir)

    source_package.source_format = "3.0 (quilt)"

    source_package.control.source = SourceParagraph(
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

    source_package.copyright.header = CopyrightHeader(
        upstream_name="debutizer",
        upstream_contact=["Tyler Compton <xaviosx@gmail.com>"],
        source="https://github.com/velovix/debutizer",
        license_="BSD-3-Clause",
        copyright_="Copyright 2021 Tyler Compton",
    )
    source_package.copyright.files.append(
        CopyrightFiles(
            files=["*", "debian/*"],
            copyright_="Copyright 2021 Tyler Compton",
            license_="BSD-3-Clause",
        )
    )
    source_package.copyright.licenses.append(
        CopyrightLicense(
            license_=Copyright.full_license_text("BSD-3-Clause"),
        )
    )
    source_package.set_debhelper_compat_version()

    source_package.changelog.add(
        ChangeBlock(
            version="0.14.0-1",
            urgency="medium",
            changes=["* Some changelog entry"],
            author="Tyler Compton <xaviosx@gmail.com>",
            date=datetime(2021, 11, 8, 23, 59),
        )
    )

    return source_package
