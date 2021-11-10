import argparse

from ..print_utils import Color, Format, print_color, print_done
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
        self.parser = EnvArgumentParser(
            prog="debutizer source", description="Fetches and sources APT packages"
        )

        self.add_artifacts_dir_flag()
        self.add_config_file_flag()
        self.add_package_dir_flag()

    def behavior(self, args: argparse.Namespace) -> None:
        config = self.parse_config_file(args)
        registry = Registry()
        build_dir = make_build_dir()

        Upstream.package_root = args.package_dir
        Upstream.build_root = build_dir
        SourcePackage.distribution = config.distribution

        package_dirs = find_package_dirs(args.package_dir)
        package_pys = process_package_pys(package_dirs, registry, build_dir)

        for package_py in package_pys:
            print_color(
                f"Sourcing {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

            results_dir = make_source_files(build_dir, package_py.source_package)

            copy_source_artifacts(
                results_dir=results_dir,
                artifacts_dir=args.artifacts_dir,
                distribution=config.distribution,
                component=package_py.component,
            )

        print_color("")
        print_done("Source")
