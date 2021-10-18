import argparse
import os
import shutil
from pathlib import Path

from ..errors import CommandError
from ..print_utils import Color, Format, done_message, print_color
from ..registry import Registry
from ..source_package import SourcePackage
from ..upstreams import Upstream
from .command import Command, register
from .utils import (
    build_package,
    get_package_dirs,
    make_chroot,
    make_source_files,
    process_package_pys,
)


@register("build")
class BuildCommand(Command):
    def define_args(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="debutizer build", description="Builds your APT packages"
        )

        self.add_common_args(parser)

        parser.add_argument(
            "--debug",
            action="store_true",
            default=False,
            help="Enters a shell if the build fails",
        )

        return parser

    def behavior(self, args: argparse.Namespace) -> None:
        registry = Registry()

        if args.build_dir.is_dir():
            shutil.rmtree(args.build_dir)
        args.build_dir.mkdir()

        Upstream.package_root = args.package_dir
        Upstream.build_root = args.build_dir
        SourcePackage.distribution = args.distribution

        package_dirs = get_package_dirs(args.package_dir)
        chroot_archive_path = make_chroot(args.distribution)
        package_pys = process_package_pys(package_dirs, registry, args.build_dir)

        print("")

        for package_py in package_pys:
            print_color(
                f"Building {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

            make_source_files(package_py.source_package)
            build_package(
                package_py.source_package,
                args.build_dir,
                chroot_archive_path,
            )

            _copy_build_output(
                package_build_dir=package_py.build_dir,
                artifacts_dir=args.artifacts_dir,
                distribution=args.distribution,
                component=package_py.component,
                architecture=args.architecture,
            )

            print("")
            done_message("Build")


def _copy_build_output(
    package_build_dir: Path,
    artifacts_dir: Path,
    distribution: str,
    component: str,
    architecture: str,
):
    deb_files = list(package_build_dir.glob(_BINARY_PACKAGE_GLOB))

    # Check that the expected files are present, but not _too_ present
    if len(deb_files) == 0:
        raise CommandError(
            f"The build process failed to produce any binary package "
            f"({_BINARY_PACKAGE_GLOB}) files."
        )

    binary_path = (
        artifacts_dir
        / Path("dists")
        / distribution
        / component
        / f"binary-{architecture}"
    )
    binary_path.mkdir(parents=True, exist_ok=True)
    for deb_file in deb_files:
        shutil.copy2(deb_file, binary_path)


_BINARY_PACKAGE_GLOB = "*.deb"
_SOURCE_ARCHIVE_GLOB = "*.orig.tar.*"
