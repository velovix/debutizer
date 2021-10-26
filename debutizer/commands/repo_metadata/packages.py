import gzip
import subprocess
from pathlib import Path
from typing import List

from debutizer.print_utils import Color, Format, print_color


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
        print_color(
            f"Updating the Packages file for packages in {dir_}",
            color=Color.MAGENTA,
            format_=Format.BOLD,
        )

        result = subprocess.run(
            [
                "dpkg-scanpackages",
                "--multiversion",
                dir_,
            ],
            cwd=artifacts_dir,
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        packages_file = artifacts_dir / dir_ / "Packages"
        packages_content = result.stdout.encode()
        packages_file.write_bytes(packages_content)
        packages_files.append(packages_file)

        compressed_file = packages_file.with_suffix(".gz")
        with gzip.open(compressed_file, "wb") as f:
            f.write(packages_content)
        packages_files.append(compressed_file)

    return packages_files
