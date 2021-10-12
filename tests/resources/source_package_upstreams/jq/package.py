from datetime import datetime

from debutizer.source_package import SourcePackage
from debutizer.upstreams import SourcePackageUpstream
from debutizer.version import Version

upstream = SourcePackageUpstream(
    name="jq",
    version=Version.from_string("1.6-1"),
    dsc_url="http://archive.ubuntu.com/ubuntu/pool/universe/j/jq/jq_1.6-1ubuntu0.20.04.1.dsc",
)
package_dir = upstream.fetch()

source_package = SourcePackage(package_dir)

source_package.add_to_changelog(
    version="1.6-1myorg1",
    urgency="medium",
    changes=[
        "* Repackaged this in my repository!",
        "  * Example of an indented bullet point",
        "* This method will add indentation if you leave it out",
        "* You don't need to worry about adding spacing on the top and bottom",
    ],
    author="Tyler Compton <xaviosx@gmail.com>",
    date=datetime(2021, 10, 7, 14, 24),
)
