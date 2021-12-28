from datetime import datetime

from debutizer.changelog import ChangeBlock
from debutizer.environment import Environment
from debutizer.source_package import SourcePackage
from debutizer.upstreams import SourcePackageUpstream
from debutizer.version import Version


def create_source_package(env: Environment) -> SourcePackage:
    upstream = SourcePackageUpstream(
        env=env,
        name="silversearcher-ag",
        version=Version.from_string("2.2.0-1"),
        dsc_url="http://archive.ubuntu.com/ubuntu/pool/universe/s/silversearcher-ag/silversearcher-ag_2.2.0-1.dsc",
    )
    package_dir = upstream.fetch()

    source_package = SourcePackage(env, package_dir)

    source_package.changelog.add(
        ChangeBlock(
            version="2.2.0-1myorg1",
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
    )

    return source_package
