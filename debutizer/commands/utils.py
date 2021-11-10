import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, List, Set, Union

from xdg.BaseDirectory import save_cache_path

from ..errors import CommandError, UnexpectedError
from ..package_py import PackagePy
from ..print_utils import print_color, print_notify
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


def find_package_dirs(package_dir: Path) -> List[Path]:
    """Finds directories defining packages"""
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
    """Runs the package.py file in each package directory, extracting the configuration
    provided by that file
    """
    package_pys: List[PackagePy] = []

    for package_dir in package_dirs:
        print_color("")
        print_notify(f"Reading {PackagePy.FILE_NAME} file for {package_dir.name}...")
        package_py = PackagePy(package_dir / PackagePy.FILE_NAME, build_dir)
        package_pys.append(package_py)
        registry.add(package_py.source_package)

    print_color("")

    for package_py in package_pys:
        print_notify(f"Running pre-build hook for {package_py.source_package.name}")
        package_py.pre_build(registry)
        # Save any further changes to the disk
        package_py.source_package.save()

    package_pys = _order_package_pys(package_pys)
    return package_pys


def _order_package_pys(package_pys: List[PackagePy]) -> List[PackagePy]:
    """Order packages by the order in which they need to be built based on their
    dependencies.
    """
    binary_package_names = []
    for package_py in package_pys:
        for binary_package in package_py.source_package.control.binaries:
            binary_package_names.append(binary_package.package)

    start_nodes: List[PackagePy] = []
    # Keep track of all unprocessed edges in the graph for each package
    edges: Dict[PackagePy, Set[PackagePy]] = {}

    for package_py in package_pys:
        if package_py.source_package.control.source is None:
            raise CommandError(
                f"Source package {package_py.source_package.name} is missing a source "
                f"paragraph in the control file"
            )

        depends_names = []
        for relation in package_py.source_package.control.source.all_build_depends():
            for dependency in relation:
                depends_names.append(dependency.name)

        managed_depends = set()
        for name in set(depends_names) & set(binary_package_names):
            for other in package_pys:
                other_binary_names = [
                    b.package for b in other.source_package.control.binaries
                ]
                if name in other_binary_names:
                    managed_depends.add(other)

        edges[package_py] = managed_depends

        # Add this as a start node if this package has no dependencies
        if len(managed_depends) == 0:
            start_nodes.append(package_py)

    ordered: List[PackagePy] = []

    while len(start_nodes) > 0:
        node = start_nodes.pop()
        ordered.append(node)

        reverse_depends = (p for p in package_pys if node in edges[p])
        for package in reverse_depends:
            edges[package].remove(node)
            if len(edges[package]) == 0:
                start_nodes.append(package)

    if len(ordered) != len(package_pys):
        raise CommandError(
            "Could not solve dependency graph. Is there a circular dependency?"
        )

    return ordered


def make_source_files(build_dir: Path, source_package: SourcePackage) -> Path:
    """Generates files related to the source package, specifically the Debian source
    file, the Debian archive, the source archive, and the .changes file.

    :param build_dir: The directory to do work in
    :param source_package: The source package object to generate files for
    :return: The directory under the build directory where the new files are placed
    """
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
            source_package.directory,
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
    """Builds binary packages for the given source package.

    :param source_package: The source package object to build binary packages for
    :param build_dir: The directory to do work in
    :param chroot_archive_path: A path to the pbuilder chroot archive
    :return: The directory under the build directory where the new files are placed
    """
    working_dir = source_package.directory.parent
    results_dir = build_dir / "outputs" / source_package.name
    results_dir.mkdir(parents=True, exist_ok=True)

    dsc_file = working_dir / f"{source_package.name}_{source_package.version}.dsc"

    command: List[Union[Path, str]] = ["pbuilder", "build"]

    hook_dir = Path(__file__).parent / "pbuilder_hooks"
    if not hook_dir.is_dir():
        raise UnexpectedError(
            f"The pbuilder hook dir does not exist at {hook_dir}. This suggests a "
            f"broken installation of Debutizer."
        )

    command += [
        "--hookdir",
        Path(__file__).parent / "pbuilder_hooks",
        "--buildresult",
        results_dir,
        "--basetgz",
        chroot_archive_path,
        dsc_file,
    ]

    try:
        run(
            command,
            on_failure="Failed to build the package",
            cwd=working_dir,
            root=True,
        )
    finally:
        if os.geteuid() != 0:
            # Give the current user ownership of build output
            run(
                ["chown", "--recursive", str(os.getuid()), results_dir],
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
    archive_path = _chroot_tgz_path(distribution)

    if not archive_path.is_file():
        # Create a chroot for builds to be performed in
        print_notify(f"Creating a chroot for distribution '{distribution}'")
        try:
            run(
                [
                    "pbuilder",
                    "create",
                    "--basetgz",
                    archive_path,
                    "--distribution",
                    distribution,
                ],
                on_failure="Failed to create pbuilder chroot environment",
                root=True,
            )
        except Exception:
            # Remove the partially created chroot
            archive_path.unlink()
            raise
    else:
        print_color(f"Using existing chroot at {archive_path}")

    return archive_path


def set_chroot_repos(distribution: str, repositories: List[str]) -> None:
    """Sets additional repositories for the chroot corresponding to the given
    distribution
    """
    print_notify(f"Adding APT lists to the '{distribution}' chroot:")
    apt_list = Path("/etc/apt/sources.list.d/debutizer.list")

    script = "#!/bin/sh\n"
    script += f"rm -f {apt_list}\n"
    for repo in repositories:
        script += f"echo '{repo}' >> {apt_list}\n"
        print_color(f" * {repo}")

    with temp_file(script) as script_file:
        run(
            [
                "pbuilder",
                "execute",
                "--basetgz",
                _chroot_tgz_path(distribution),
                "--save-after-exec",
                "--",
                script_file,
            ],
            on_failure="Failed to set APT repositories in the chroot",
            root=True,
        )


def copy_source_artifacts(
    results_dir: Path,
    artifacts_dir: Path,
    distribution: str,
    component: str,
) -> None:
    """Copies source files to their proper location in the artifacts directory.

    :param results_dir: The path where the source files are
    :param artifacts_dir: The artifacts directory
    :param distribution: The distribution these packages are for
    :param component: The repository component that this package is under
    """
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
    """Copies binary package files to their proper location in the artifacts directory.

    :param results_dir: The path where the binary package files are
    :param artifacts_dir: The artifacts directory
    :param distribution: The distribution these packages are for
    :param component: The repository component that this package is under
    :param architecture: The CPU architecture these binary artifacts are for
    """
    deb_files = find_binary_packages(results_dir)

    # Check that the expected files are present
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
def temp_file(content: str) -> Iterator[Path]:
    _, file_ = tempfile.mkstemp()
    path = Path(file_)

    with path.open("w") as f:
        f.write(content)

    yield path

    path.unlink()


def make_build_dir() -> Path:
    build_dir = Path(save_cache_path("debutizer"))
    if build_dir.is_dir():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    return build_dir


def _chroot_tgz_path(distribution: str) -> Path:
    pbuilder_cache_str = os.environ.get(
        "DEBUTIZER_PBUILDER_CACHE_DIR", "/var/cache/pbuilder"
    )
    pbuilder_cache_path = Path(pbuilder_cache_str)
    return pbuilder_cache_path / f"debutizer-{distribution}.tgz"
