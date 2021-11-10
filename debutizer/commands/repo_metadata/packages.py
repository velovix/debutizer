import subprocess
from pathlib import Path
from typing import List

from debutizer.print_utils import print_notify
from debutizer.subprocess_utils import run

from .utils import save_metadata_files


def add_packages_files(artifacts_dir: Path) -> List[Path]:
    """Adds Packages files to the given APT package file tree. Packages files provide
    listings for binary packages. One Packages file is made per binary package
    directory, and they are placed in
    "dists/{distro}/{component/binary-{arch}/Packages".

    :param artifacts_dir: The root of the APT package file tree
    :return: The newly created Packages files
    """

    packages_files = []

    # Find all binary package directories for all distributions, components, and
    # architectures. These are paths like: dists/bionic/main/binary-amd64
    dirs = artifacts_dir.glob("dists/*/*/binary-*")
    dirs = (d.relative_to(artifacts_dir) for d in dirs)

    for dir_ in dirs:
        result = run(
            [
                "dpkg-scanpackages",
                "--multiversion",
                dir_,
            ],
            on_failure="Failed to update the Packages file",
            cwd=artifacts_dir,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        packages_file = artifacts_dir / dir_ / "Packages"
        packages_files += save_metadata_files(packages_file, result.stdout)

    return packages_files
