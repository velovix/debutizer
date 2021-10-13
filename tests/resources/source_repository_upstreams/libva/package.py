from datetime import datetime

from debutizer.source_package import SourcePackage
from debutizer.upstreams import SourceRepositoryUpstream
from debutizer.version import Version

upstream = SourceRepositoryUpstream(
    name="libva",
    version=Version.from_string("2.7.0-2"),
    repository_url="https://github.com/intel/libva",
    revision_format="{upstream_version}",
)
package_dir = upstream.fetch()

source_package = SourcePackage(package_dir)

source_package.changelog.add(
    version="2.7.0-2myorg1",
    urgency="medium",
    changes=["* Repackaged this in my repository!"],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 10, 8, 16, 21),
)
