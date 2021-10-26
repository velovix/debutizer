import subprocess
from pathlib import Path
from typing import List

from debutizer.print_utils import Color, Format, print_color


def add_sources_files(artifacts_dir: Path) -> List[Path]:
    """Adds Sources files to the given APT package file tree. Sources files provide
    listings for source packages. One Sources file is made per source directory, and
    they are placed in "dists/{distro}/{component}/Sources".

    :param artifacts_dir: The root of the APT package file tree
    :return: The newly created Sources files
    """

    sources_files = []

    # Find all source package directories for all distributions and components. These
    # are paths like: dists/bionic/main/source
    dirs = artifacts_dir.glob("dists/*/*/source")
    dirs = (d.relative_to(artifacts_dir) for d in dirs)

    for dir_ in dirs:
        print_color(
            f"Updating the Sources file for packages in {dir_}",
            color=Color.MAGENTA,
            format_=Format.BOLD,
        )

        result = subprocess.run(
            [
                "dpkg-scansources",
                dir_,
            ],
            cwd=artifacts_dir,
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        sources_file = artifacts_dir / dir_ / "Sources"
        sources_file.write_text(result.stdout)
        sources_files.append(sources_file)

    return sources_files
