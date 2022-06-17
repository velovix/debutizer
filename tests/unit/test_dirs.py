from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from debutizer.dirs import Dirs


def test_dirs_parsing() -> None:
    """Tests that the Dirs class loads a dirs file properly"""

    with _package_dir() as package_dir:
        dirs_file = package_dir / Dirs.FILE_PATH

        dirs = Dirs(package_dir)

        dirs.load()

        assert len(dirs) == 2
        assert dirs[0] == Path("/var/lib/something")
        assert dirs[1] == Path("/etc/cooldir")

        dirs.save()

        assert dirs_file.read_text() == _DIRS_STR.strip()


def test_dirs_retains_everything() -> None:
    """Tests that, after being parsed and dumped back into the file system, all data in
    the dirs file is retained
    """
    with _package_dir() as package_dir:
        dirs_file = package_dir / Dirs.FILE_PATH

        dirs = Dirs(package_dir)
        dirs.load()
        dirs.save()

        assert dirs_file.read_text() == _DIRS_STR.strip()


@contextmanager
def _package_dir():
    """Creates a temporary directory with an example dirs file inside it"""

    with TemporaryDirectory() as dir_str:
        dir_ = Path(dir_str)
        changelog_file = dir_ / Dirs.FILE_PATH
        changelog_file.parent.mkdir()
        changelog_file.write_text(_DIRS_STR)

        yield dir_


_DIRS_STR = """/var/lib/something
/etc/cooldir
"""
