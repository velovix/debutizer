import argparse

from ..environment import Environment
from ..print_utils import print_color, print_done, print_header, print_notify
from ..registry import Registry
from ..source_package import SourcePackage
from ..upstreams import Upstream
from .command import Command
from .env_argparse import EnvArgumentParser
from .utils import (
    copy_source_artifacts,
    find_package_dirs,
    make_build_dir,
    make_source_files,
    process_package_pys,
)


class SourceCommand(Command):
    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer source", description="Makes source packages"
        )

        self.add_artifacts_dir_flag()
        self.add_config_file_flag()
        self.add_package_dir_flag()

    def behavior(self, args: argparse.Namespace) -> None:
        config = self.parse_config_file(args)
        registry = Registry()

        for distro in config.distributions:
            _source_packages(args=args, registry=registry, distribution=distro)

        print_color("")
        print_done("Source complete!")


def _source_packages(
    args: argparse.Namespace, registry: Registry, distribution: str
) -> None:
    print_header(f"Sourcing packages for distribution {distribution}")

    Environment.codename = distribution

    build_dir = make_build_dir()

    Upstream.package_root = args.package_dir
    Upstream.build_root = build_dir
    SourcePackage.distribution = distribution

    package_dirs = find_package_dirs(args.package_dir)
    package_pys = process_package_pys(package_dirs, registry, build_dir)

    for package_py in package_pys:
        print_notify(f"Sourcing {package_py.source_package.name}")

        results_dir = make_source_files(build_dir, package_py.source_package)

        copy_source_artifacts(
            results_dir=results_dir,
            artifacts_dir=args.artifacts_dir,
            distribution=distribution,
            component=package_py.component,
        )
