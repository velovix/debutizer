from pathlib import Path
from typing import List


def find_binary_packages(path: Path, recursive: bool = False) -> List[Path]:
    return _glob_search(path, BINARY_PACKAGE_GLOB, recursive)


def find_debian_source_files(path: Path, recursive: bool = False) -> List[Path]:
    return _glob_search(path, DEBIAN_SOURCE_FILE_GLOB, recursive)


def find_source_archives(path: Path, recursive: bool = False) -> List[Path]:
    return _glob_search(path, SOURCE_ARCHIVE_GLOB, recursive)


def find_debian_archives(path: Path, recursive: bool = False) -> List[Path]:
    return _glob_search(path, DEBIAN_ARCHIVE_GLOB, recursive)


def find_archives(path: Path, recursive: bool = False) -> List[Path]:
    return (
        find_binary_packages(path, recursive)
        + find_debian_source_files(path, recursive)
        + find_source_archives(path, recursive)
        + find_debian_archives(path, recursive)
    )


def _glob_search(path: Path, glob: str, recursive: bool) -> List[Path]:
    if recursive:
        output = path.rglob(glob)
    else:
        output = path.glob(glob)

    return list(output)


BINARY_PACKAGE_GLOB = "*.deb"
DEBIAN_SOURCE_FILE_GLOB = "*.dsc"
SOURCE_ARCHIVE_GLOB = "*.orig.tar.*"
DEBIAN_ARCHIVE_GLOB = "*.debian.tar.*"
