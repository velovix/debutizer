import argparse
import shutil
from pathlib import Path

from ..errors import CommandError, UnexpectedError
from ..print_utils import Color, Format, done_message, print_color
from ..registry import Registry
from ..source_package import SourcePackage
from ..upstreams import Upstream
from .command import Command, register
from .utils import (
    DEBIAN_ARCHIVE_GLOB,
    DEBIAN_SOURCE_FILE_GLOB,
    SOURCE_ARCHIVE_GLOB,
    get_package_dirs,
    make_chroot,
    make_source_files,
    process_package_pys,
)


@register("source")
class SourceCommand(Command):
    def define_args(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="debutizer source", description="Fetches and sources your APT packages"
        )

        self.add_common_args(parser)

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

        for package_py in package_pys:
            print_color(
                f"Sourcing {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

            make_source_files(package_py.source_package)

            _copy_build_output(
                package_build_dir=package_py.build_dir,
                artifacts_dir=args.artifacts_dir,
                distribution=args.distribution,
                component=package_py.component,
            )

        print("")
        done_message("Source")


def _copy_build_output(
    package_build_dir: Path,
    artifacts_dir: Path,
    distribution: str,
    component: str,
):
    dsc_files = list(package_build_dir.glob(DEBIAN_SOURCE_FILE_GLOB))
    orig_tar_files = list(package_build_dir.glob(SOURCE_ARCHIVE_GLOB))
    debian_tar_files = list(package_build_dir.glob(DEBIAN_ARCHIVE_GLOB))

    # Check that the expected files are present, but not _too_ present
    if len(dsc_files) == 0:
        raise CommandError(
            f"The build process failed to produce a Debian source "
            f"({DEBIAN_SOURCE_FILE_GLOB}) file."
        )
    elif len(dsc_files) > 1:
        raise UnexpectedError(
            f"The build process produced more than one Debian source "
            f"({DEBIAN_SOURCE_FILE_GLOB}) file. This shouldn't be possible, as "
            f"only one source package can be built at a time."
        )
    if len(orig_tar_files) == 0:
        raise CommandError(
            f"The build process failed to produce a source archive "
            f"({SOURCE_ARCHIVE_GLOB}) file. "
        )
    elif len(orig_tar_files) > 1:
        raise UnexpectedError(
            f"The build process produced more than one source archive "
            f"({SOURCE_ARCHIVE_GLOB}) file. This shouldn't be possible, as only "
            f"one source package can be built at a time."
        )
    if len(debian_tar_files) == 0:
        raise CommandError(
            f"The build process failed to produce a Debian archive "
            f"({DEBIAN_ARCHIVE_GLOB}) file."
        )
    elif len(debian_tar_files) > 1:
        raise UnexpectedError(
            f"The build process produced more than one Debian archive "
            f"({DEBIAN_ARCHIVE_GLOB}) file. This shouldn't be possible as only "
            "one source package can be built at a time."
        )

    source_path = artifacts_dir / Path("dists") / distribution / component / "source"
    source_path.mkdir(parents=True, exist_ok=True)
    for source_file in dsc_files + orig_tar_files + debian_tar_files:
        shutil.copy2(source_file, source_path)
