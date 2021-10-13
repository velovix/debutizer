import argparse
import os
import platform
import shutil
from pathlib import Path
from typing import List

from xdg import xdg_cache_home

from ..errors import CommandError, UnexpectedError
from ..package_py import PackagePy
from ..print_utils import Color, Format, done_message, print_color
from ..registry import Registry
from ..source_package import SourcePackage
from ..subprocess_utils import run
from ..upstreams import Upstream
from .command import Command, register


@register("build")
class BuildCommand(Command):
    def define_args(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="debutizer build", description="Builds APT packages"
        )

        parser.add_argument(
            "--package-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_PACKAGE_DIR", Path.cwd() / "packages"),
            required=False,
            help="The directory that holds the package directories",
        )

        default_build_dir = xdg_cache_home() / "debutizer"
        parser.add_argument(
            "--build-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_BUILD_DIR", default_build_dir),
            required=False,
            help="The directory that will hold intermediate build files",
        )

        parser.add_argument(
            "--artifacts-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_ARTIFACTS_DIR", Path.cwd() / "artifacts"),
            required=False,
            help="The directory that will hold the resulting packages and other "
            "artifacts",
        )

        parser.add_argument(
            "--distribution",
            type=str,
            required=True,
            help="The codename of the distribution to build packages against, like "
            "'focal' or 'sid'.",
        )

        # TODO: Update the help text when cross-building is supported. qemubuilder?
        parser.add_argument(
            "--architecture",
            type=str,
            required=False,
            default=_host_architecture(),
            help="The architecture to build packages against, like 'amd64' or 'arm64'. "
            "Defaults to the host architecture. Changing this value will currently "
            "break your build.",
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            default=False,
            help="Enters a shell if the build fails",
        )

        return parser

    def behavior(self, args: argparse.Namespace) -> None:
        if args.build_dir.is_dir():
            shutil.rmtree(args.build_dir)
        args.build_dir.mkdir()

        Upstream.package_root = args.package_dir
        Upstream.build_root = args.build_dir
        SourcePackage.distribution = args.distribution

        package_dirs = args.package_dir.iterdir()
        package_dirs = list(filter(Path.is_dir, package_dirs))

        if len(package_dirs) == 0:
            raise CommandError("No directories in package path")

        package_configs: List[PackagePy] = []
        registry = Registry()

        chroot_archive_path = _make_chroot(args.distribution)

        for package_dir in package_dirs:
            print("")
            print_color(
                f"Reading {PackagePy.FILE_NAME} file for {package_dir.name}...",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )
            package_py = PackagePy(package_dir / PackagePy.FILE_NAME)
            package_configs.append(package_py)
            registry.add(package_py.source_package)

        print("")

        for package_py in package_configs:
            print_color(
                f"Running pre-build hook for {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )
            package_py.pre_build(registry)

        print("")

        for package_py in package_configs:
            print_color(
                f"Building {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

            # Check if a debian/ directory exists
            debian_dir = package_py.source_package.package_dir / "debian"
            if not debian_dir.is_dir():
                raise CommandError(
                    f"No 'debian' directory is present in {debian_dir.parent}"
                )

            working_dir = package_py.source_package.package_dir

            # Generate the Debian source file and Debian archive
            run(
                [
                    "dpkg-source",
                    "--build",
                    str(working_dir),
                ],
                on_failure="Failed to generate Debian source files",
                cwd=working_dir.parent,
            )

            # Run the build
            dsc_file_name = f"{package_py.source_package.name}_{package_py.source_package.version}.dsc"
            output_dir = args.build_dir / f"{package_py.source_package.name}-output"
            output_dir.mkdir()
            try:
                run(
                    [
                        "pbuilder",
                        "build",
                        "--buildresult",
                        str(output_dir),
                        "--basetgz",
                        str(chroot_archive_path),
                        str(working_dir.parent / dsc_file_name),
                    ],
                    on_failure="Failed to build the package",
                    cwd=working_dir.parent,
                    root=True,
                )
            finally:
                if os.geteuid() != 0:
                    # Give the current user ownership of build output
                    run(
                        ["chown", "--recursive", str(os.getuid()), str(args.build_dir)],
                        on_failure="Failed to fix permissions for the build path",
                        root=True,
                    )

            # pbuilder does not reproduce the source archive, copy it manually
            for orig_archive in working_dir.parent.glob(_SOURCE_ARCHIVE_GLOB):
                shutil.copy2(orig_archive, output_dir)

            _copy_build_output(
                output_dir=output_dir,
                artifacts_dir=args.artifacts_dir,
                distribution=args.distribution,
                component=package_py.component,
                architecture=args.architecture,
            )

            print("")
            done_message("Build")


def _make_chroot(distribution: str) -> Path:
    """Creates a chroot environment for the package to be built in, if one does not
    already exist.

    :param distribution: The distribution codename to create a chroot for
    :return: A path to the archive containing the chroot contents
    """
    pbuilder_cache_str = os.environ.get(
        "DEBUTIZER_PBUILDER_CACHE_DIR", "/var/cache/pbuilder"
    )
    pbuilder_cache_path = Path(pbuilder_cache_str)
    archive_path = pbuilder_cache_path / f"debutizer-{distribution}.tgz"

    if not archive_path.is_file():
        # Create a chroot for builds to be performed in
        print_color(
            f"Creating a chroot for distribution '{distribution}'",
            color=Color.MAGENTA,
            format_=Format.BOLD,
        )
        run(
            [
                "pbuilder",
                "create",
                "--basetgz",
                str(archive_path),
                "--distribution",
                distribution,
            ],
            on_failure="Failed to create pbuilder chroot environment",
            root=True,
        )
    else:
        print(f"Using existing chroot at {archive_path}")

    return archive_path


def _copy_build_output(
    output_dir: Path,
    artifacts_dir: Path,
    distribution: str,
    component: str,
    architecture: str,
):
    deb_files = list(output_dir.glob(_BINARY_PACKAGE_GLOB))
    dsc_files = list(output_dir.glob(_DEBIAN_SOURCE_FILE_GLOB))
    orig_tar_files = list(output_dir.glob(_SOURCE_ARCHIVE_GLOB))
    debian_tar_files = list(output_dir.glob(_DEBIAN_ARCHIVE_GLOB))

    # Check that the expected files are present, but not _too_ present
    if len(deb_files) == 0:
        raise CommandError(
            f"The build process failed to produce any binary package "
            f"({_BINARY_PACKAGE_GLOB}) files."
        )
    if len(dsc_files) == 0:
        raise CommandError(
            f"The build process failed to produce a Debian source "
            f"({_DEBIAN_SOURCE_FILE_GLOB}) file."
        )
    elif len(dsc_files) > 1:
        raise UnexpectedError(
            f"The build process produced more than one Debian source "
            f"({_DEBIAN_SOURCE_FILE_GLOB}) file. This shouldn't be possible, as "
            f"only one source package can be built at a time."
        )
    if len(orig_tar_files) == 0:
        raise CommandError(
            f"The build process failed to produce a source archive "
            f"({_SOURCE_ARCHIVE_GLOB}) file. "
        )
    elif len(orig_tar_files) > 1:
        raise UnexpectedError(
            f"The build process produced more than one source archive "
            f"({_SOURCE_ARCHIVE_GLOB}) file. This shouldn't be possible, as only "
            f"one source package can be built at a time."
        )
    if len(debian_tar_files) == 0:
        raise CommandError(
            f"The build process failed to produce a Debian archive "
            f"({_DEBIAN_ARCHIVE_GLOB}) file."
        )
    elif len(debian_tar_files) > 1:
        raise UnexpectedError(
            f"The build process produced more than one Debian archive "
            f"({_DEBIAN_ARCHIVE_GLOB}) file. This shouldn't be possible as only "
            "one source package can be built at a time."
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

    source_path = artifacts_dir / Path("dists") / distribution / component / "source"
    source_path.mkdir(parents=True, exist_ok=True)
    for source_file in dsc_files + orig_tar_files + debian_tar_files:
        shutil.copy2(source_file, source_path)


def _host_architecture() -> str:
    """
    :return: Debian's name for the host CPU architecture
    """
    arch = platform.machine()

    # Python uses the GNU names for architectures, which is sometimes different from
    # Debian's names. This is documented in /usr/share/dpkg/cputable.
    if arch == "x86_64":
        return "amd64"
    elif arch == "aarch64":
        return "amd64"
    else:
        return arch


_BINARY_PACKAGE_GLOB = "*.deb"
_DEBIAN_SOURCE_FILE_GLOB = "*.dsc"
_SOURCE_ARCHIVE_GLOB = "*.orig.tar.*"
_DEBIAN_ARCHIVE_GLOB = "*.debian.tar.*"
