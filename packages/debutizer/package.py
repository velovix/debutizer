from datetime import datetime

from debutizer.copyright import Copyright
from debutizer.source_package import SourcePackage
from debutizer.upstreams import SourceRepositoryUpstream
from debutizer.version import Version

upstream = SourceRepositoryUpstream(
    name="debutizer",
    version=Version.from_string("0.1.0-1"),
    repository_url="https://github.com/velovix/debutizer",
    revision_format="v{upstream_version}",
)
package_dir = upstream.fetch()

source_package = SourcePackage(package_dir, complete=False)

source_package.set_source_format()

source_package.control.set_source_package(
    maintainer="Tyler Compton <xaviosx@gmail.com>",
    section="utils",
    priority="optional",
    build_depends=[
        "debhelper-compat (= 12)",
        "dh-python",
        "python3-all",
        "python3-pytest",
        "python3-setuptools",
        "python3-debian",
        "python3-xdg",
        "python3-requests",
    ],
    uploaders=["Tyler Compton <xaviosx@gmail.com>"],
    homepage="https://github.com/velovix/debutizer",
)
source_package.control.add_binary_package(
    package="debutizer",
    architecture="any",
    description="A tool for managing APT packages",
    section="utils",
    priority="optional",
    depends=[
        "${python3:Depends}",
        "${misc:Depends}",
        "pbuilder",
        "devscripts",
        "quilt",
    ],
    recommends=[
        "debian-keyring",
    ],
    homepage="https://github.com/velovix/debutizer",
)

source_package.copyright.set_header(
    upstream_name="debutizer",
    upstream_contact=["Tyler Compton <xaviosx@gmail.com>"],
    source="https://github.com/velovix/debutizer",
    license_="BSD-3-Clause",
    copyright_="Copyright 2021 Tyler Compton",
)
source_package.copyright.add_files(
    files=["*", "debian/*"],
    copyright_="Copyright 2021 Tyler Compton",
    license_="BSD-3-Clause",
)
source_package.copyright.add_license(
    license_=Copyright.full_license_text("BSD-3-Clause"),
)

source_package.changelog.add(
    version="0.1.0-1",
    urgency="medium",
    changes=["* Initial packaging"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 10, 11, 22, 46),
)

source_package.complete()