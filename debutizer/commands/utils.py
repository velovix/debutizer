import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List

from ..errors import CommandError, UnexpectedError
from ..package_py import PackagePy
from ..print_utils import Color, Format, print_color
from ..registry import Registry
from ..source_package import SourcePackage
from ..subprocess_utils import run
from .artifacts import (
    BINARY_PACKAGE_GLOB,
    DEBIAN_ARCHIVE_GLOB,
    DEBIAN_SOURCE_FILE_GLOB,
    SOURCE_ARCHIVE_GLOB,
    find_binary_packages,
    find_debian_archives,
    find_debian_source_files,
    find_source_archives,
)


def get_package_dirs(package_dir: Path) -> List[Path]:
    if not package_dir.is_dir():
        raise CommandError(f"The package directory '{package_dir}' does not exist")

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


def make_source_files(build_dir: Path, source_package: SourcePackage) -> Path:
    results_dir = build_dir / "outputs" / source_package.name
    results_dir.mkdir(parents=True, exist_ok=True)
    working_dir = source_package.directory.parent

    # Check if a debian/ directory exists
    debian_dir = source_package.directory / "debian"
    if not debian_dir.is_dir():
        raise CommandError(f"No 'debian' directory is present in {debian_dir.parent}")

    # Generate the Debian source file and Debian archive
    run(
        [
            "dpkg-source",
            "--compression=xz",
            "--build",
            str(source_package.directory),
        ],
        on_failure="Failed to generate Debian source files",
        cwd=working_dir,
    )
    dsc_file = working_dir / f"{source_package.name}_{source_package.version}.dsc"
    if not dsc_file.is_file():
        raise CommandError(
            f"dpkg-source failed to generate a Debian source file. Expected one at "
            f"{dsc_file}."
        )
    shutil.copy2(str(dsc_file), str(results_dir))
    debian_archive_file = (
        working_dir / f"{source_package.name}_{source_package.version}.debian.tar.xz"
    )
    if not debian_archive_file.is_file():
        raise CommandError(
            f"dpkg-source failed to generate a Debian archive file. Expected one at "
            f"{debian_archive_file}."
        )
    shutil.copy2(str(debian_archive_file), str(results_dir))

    changes_file = results_dir / f"{source_package.name}_source.changes"
    run(
        [
            "dpkg-genchanges",
            "--build=source",
            f"-O{changes_file}",
        ],
        on_failure="Failed to generate a .changes file",
        cwd=source_package.directory,
    )
    if not changes_file.is_file():
        raise CommandError(
            f"dpkg-genchanges failed to generate a changes file. Expected one at "
            f"{changes_file}."
        )

    # Copy the source archive created by the upstream into the results directory
    glob_str = f"{source_package.name}_*.orig.tar.*"
    glob_results = list(working_dir.glob(glob_str))
    if len(glob_results) == 0:
        raise CommandError(
            f"The upstream failed to generate a source archive file. Expected one at "
            f"{working_dir / glob_str}."
        )
    shutil.copy2(str(glob_results[0]), str(results_dir))

    return results_dir


def build_package(
    source_package: SourcePackage,
    build_dir: Path,
    chroot_archive_path: Path,
) -> Path:
    working_dir = source_package.directory.parent
    results_dir = build_dir / "outputs" / source_package.name
    results_dir.mkdir(parents=True, exist_ok=True)

    # Run the build
    dsc_file = working_dir / f"{source_package.name}_{source_package.version}.dsc"
    try:
        run(
            [
                "pbuilder",
                "build",
                "--buildresult",
                str(results_dir),
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
                ["chown", "--recursive", str(os.getuid()), str(results_dir)],
                on_failure="Failed to fix permissions for the build path",
                root=True,
            )

    return results_dir


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


def copy_source_artifacts(
    results_dir: Path,
    artifacts_dir: Path,
    distribution: str,
    component: str,
):
    dsc_files = find_debian_source_files(results_dir)
    orig_tar_files = find_source_archives(results_dir)
    debian_tar_files = find_debian_archives(results_dir)

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


def copy_binary_artifacts(
    results_dir: Path,
    artifacts_dir: Path,
    distribution: str,
    component: str,
    architecture: str,
):
    deb_files = find_binary_packages(results_dir)

    # Check that the expected files are present, but not _too_ present
    if len(deb_files) == 0:
        raise CommandError(
            f"The build process failed to produce any binary package "
            f"({BINARY_PACKAGE_GLOB}) files."
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


@contextmanager
def sensitive_temp_file(content: str) -> Iterator[Path]:
    _, file_ = tempfile.mkstemp()
    path = Path(file_)

    with path.open("w") as f:
        f.write(content)

    yield path

    path.unlink()
