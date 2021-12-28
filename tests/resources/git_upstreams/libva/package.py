from datetime import datetime

from debutizer.changelog import ChangeBlock
from debutizer.environment import Environment
from debutizer.source_package import SourcePackage
from debutizer.upstreams import GitUpstream
from debutizer.version import Version


def create_source_package(env: Environment) -> SourcePackage:
    upstream = GitUpstream(
        env=env,
        name="libva",
        version=Version.from_string("2.7.0"),
        repository_url="https://github.com/intel/libva",
        revision="{upstream_version}",
    )
    package_dir = upstream.fetch()

    source_package = SourcePackage(env, package_dir)

    source_package.changelog.add(
        ChangeBlock(
            version="2.7.0-2myorg1",
            urgency="medium",
            changes=["* Repackaged this in my repository!"],
            author="Tyler Compton <xaviosx@gmail.com>",
            date=datetime(2021, 10, 8, 16, 21),
        )
    )

    return source_package
