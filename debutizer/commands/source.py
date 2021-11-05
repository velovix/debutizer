import argparse
import shutil

from ..print_utils import Color, Format, print_color, print_done
from ..registry import Registry
from ..source_package import SourcePackage
from ..upstreams import Upstream
from .command import Command
from .config import EnvArgumentParser
from .utils import (
    copy_source_artifacts,
    find_package_dirs,
    make_source_files,
    process_package_pys,
)


class SourceCommand(Command):
    def __init__(self):
        self.parser = EnvArgumentParser(
            prog="debutizer source", description="Fetches and sources APT packages"
        )

        self.add_common_args()

    def behavior(self, args: argparse.Namespace) -> None:
        registry = Registry()

        if args.build_dir.is_dir():
            shutil.rmtree(args.build_dir)
        args.build_dir.mkdir()

        Upstream.package_root = args.package_dir
        Upstream.build_root = args.build_dir
        SourcePackage.distribution = args.distribution

        package_dirs = find_package_dirs(args.package_dir)
        package_pys = process_package_pys(package_dirs, registry, args.build_dir)

        for package_py in package_pys:
            print_color(
                f"Sourcing {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

            results_dir = make_source_files(args.build_dir, package_py.source_package)

            copy_source_artifacts(
                results_dir=results_dir,
                artifacts_dir=args.artifacts_dir,
                distribution=args.distribution,
                component=package_py.component,
            )

        print_color("")
        print_done("Source")
