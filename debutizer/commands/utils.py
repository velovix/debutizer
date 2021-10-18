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
    run(
        [
            "dpkg-genchanges",
            "--build=source",
            f"-O../{source_package.name}_source.changes",
            # str(source_package.directory),
        ],
        on_failure="Failed to generate a .changes file",
        cwd=source_package.directory,
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


def make_chroot(distribution: str) -> Path:
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


DEBIAN_SOURCE_FILE_GLOB = "*.dsc"
SOURCE_ARCHIVE_GLOB = "*.orig.tar.*"
DEBIAN_ARCHIVE_GLOB = "*.debian.tar.*"
