from datetime import datetime

from debutizer.source_package import SourcePackage
from debutizer.upstreams import SourceRepositoryUpstream
from debutizer.version import Version

upstream = SourceRepositoryUpstream(
    name="debutizer",
    version=Version.from_string("0.1.0-1"),
    repository_url="https://github.com/intel/libva",
    revision_format="v{upstream_version}",
)
package_dir = upstream.fetch()

source_package = SourcePackage(package_dir)

source_package.set_source_format()

source_package.set_source_package(
    maintainer="Tyler Compton <xaviosx@gmail.com>",
    section="utils",
    priority="optional",
    build_depends=[
        # TODO: I probably need something here. That Python utility thing?
    ],
    uploaders=["Tyler Compton <xaviosx@gmail.com>"],
    homepage="https://github.com/velovix/debutizer",
)
source_package.add_binary_package(
    package="debutizer",
    architecture="any",
    description="A tool for managing APT packages",
    section="utils",
    priority="optional",
    depends=[
        "pbuilder",
        "devscripts",
        "quilt",
        "python3-apt",
        "python3-debian",
        "python3-xdg",
    ],
    recommends=[
        "debian-keyring",
    ],
    homepage="https://github.com/velovix/debutizer",
)

source_package.set_copyright_header(
    upstream_name="debutizer",
    upstream_contact=["Tyler Compton <xaviosx@gmail.com>"],
    source="https://github.com/velovix/debutizer",
    license_="BSD-3-clause",  # TODO: Full text
    copyright_="Copyright 2021 Tyler Compton",
)

source_package.add_to_changelog(
    version="0.1.0-1",
    urgency="medium",
    changes=["* Initial packaging"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 10, 11, 22, 46),
)

source_package.complete()
