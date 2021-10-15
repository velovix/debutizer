import os
import shutil
from pathlib import Path
from typing import List

from ..errors import CommandError
from ..package_py import PackagePy
from ..print_utils import Color, Format, print_color
from ..registry import Registry
from ..source_package import SourcePackage
from ..subprocess_utils import run


def get_package_dirs(package_dir: Path) -> List[Path]:
    package_dirs = list(filter(Path.is_dir, package_dir.iterdir()))

    if len(package_dirs) == 0:
        raise CommandError("No directories in package path")

    return package_dirs


def process_package_pys(
    package_dirs: List[Path],
    registry: Registry,
    build_dir: Path,
) -> List[PackagePy]:
    package_configs: List[PackagePy] = []

    for package_dir in package_dirs:
        print("")
        print_color(
            f"Reading {PackagePy.FILE_NAME} file for {package_dir.name}...",
            color=Color.MAGENTA,
            format_=Format.BOLD,
        )
        package_py = PackagePy(package_dir / PackagePy.FILE_NAME, build_dir)
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

    return package_configs


def make_source_files(source_package: SourcePackage) -> None:
    # Check if a debian/ directory exists
    debian_dir = source_package.directory / "debian"
    if not debian_dir.is_dir():
        raise CommandError(f"No 'debian' directory is present in {debian_dir.parent}")

    # Generate the Debian source file and Debian archive
    run(
        [
            "dpkg-source",
            "--build",
            str(source_package.directory),
        ],
        on_failure="Failed to generate Debian source files",
        cwd=source_package.directory.parent,
    )


def build_package(
    source_package: SourcePackage,
    build_dir: Path,
    chroot_archive_path: Path,
) -> None:
    working_dir = source_package.directory.parent

    # Run the build
    dsc_file = working_dir / f"{source_package.name}_{source_package.version}.dsc"
    try:
        run(
            [
                "pbuilder",
                "build",
                "--buildresult",
                str(working_dir),
                "--basetgz",
                str(chroot_archive_path),
                str(dsc_file),
            ],
            on_failure="Failed to build the package",
            cwd=working_dir,
            root=True,
        )
    finally:
        if os.geteuid() != 0:
            # Give the current user ownership of build output
            run(
                ["chown", "--recursive", str(os.getuid()), str(build_dir)],
                on_failure="Failed to fix permissions for the build path",
                root=True,
            )

    # pbuilder does not reproduce the source archive, copy it manually
    # for orig_archive in working_dir.glob(SOURCE_ARCHIVE_GLOB):
    #     shutil.copy2(orig_archive, output_dir)


DEBIAN_SOURCE_FILE_GLOB = "*.dsc"
SOURCE_ARCHIVE_GLOB = "*.orig.tar.*"
DEBIAN_ARCHIVE_GLOB = "*.debian.tar.*"
