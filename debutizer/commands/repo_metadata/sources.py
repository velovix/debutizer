import subprocess
from pathlib import Path
from typing import List

from debutizer.print_utils import print_notify
from debutizer.subprocess_utils import run

from .utils import save_metadata_files


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
        result = run(
            [
                "dpkg-scansources",
                dir_,
            ],
            on_failure="Failed to update the Sources file",
            cwd=artifacts_dir,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        sources_file = artifacts_dir / dir_ / "Sources"
        sources_files += save_metadata_files(sources_file, result.stdout)

    return sources_files
