from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from debutizer.changelog import ChangeBlock, Changelog


def test_changelog_retains_everything():
    """Tests that, after being parsed and dumped back to the file system, all data and
    formatting on the changelog is retained
    """
    with _package_dir() as package_dir:
        changelog_file = package_dir / Changelog.FILE_PATH

        changelog = Changelog(
            package_dir=package_dir, distribution="unstable", package="gstreamer1.0"
        )
        changelog.load()
        changelog.save()

        assert changelog_file.read_text() == _CHANGELOG_STR


def test_changelog_latest_version():
    """Tests that the changelog consults the top entry for the latest version"""
    with _package_dir() as package_dir:
        changelog = Changelog(
            package_dir=package_dir, distribution="unstable", package="gstreamer1.0"
        )
        changelog.load()

        assert changelog.version == "1.18.4-1"


def test_changelog_defaults():
    """Tests that changelog blocks can be added without some fields, and that those
    fields will be filled in by defaults given to the Changelog object
    """
    changelog = Changelog(
        package_dir=Path(""), distribution="focal", package="libtoocool"
    )

    # Add an entry with the distribution and package name defined, where defaults should
    # not be used
    changelog.add(
        ChangeBlock(
            version="0.9.0-1",
            urgency="medium",
            changes=[
                "* Fix race condition when parsing multiple streams with the same name"
            ],
            author="Mr. Developer Man <devman@seriouscompany.biz>",
            date=datetime(2002, 11, 3, 3, 0),
            package="libtwolame",
            distribution="bionic",
        )
    )
    assert changelog.blocks[0].distribution == "bionic"
    assert changelog.blocks[0].package == "libtwolame"

    # Add an entry with no distribution or package name and ensure the defaults
    # are used
    changelog.add(
        ChangeBlock(
            version="1.0.0-1",
            urgency="medium",
            changes=[
                "* Made the project name much cooler",
            ],
            author="Joe Cool <lilcoolj1992@yahoo.com>",
            date=datetime(2002, 12, 25, 8, 30),
        )
    )
    assert changelog.blocks[0].distribution == "focal"
    assert changelog.blocks[0].package == "libtoocool"


@contextmanager
def _package_dir():
    """Creates a temporary directory with an example changelog inside it"""

    with TemporaryDirectory() as dir_str:
        dir_ = Path(dir_str)
        changelog_file = dir_ / Changelog.FILE_PATH
        changelog_file.parent.mkdir()
        changelog_file.write_text(_CHANGELOG_STR)

        yield dir_


_CHANGELOG_STR = """gstreamer1.0 (1.18.4-1) experimental; urgency=medium

  [ Helmut Grohne ]
  * Annotate Build-Depends libgmp-dev and libgsl-dev
    <!nocheck> (Closes: #981203).

  [ Marc Leeman ]
  * New upstream version 1.18.4

  [ Sebastian Dröge ]
  * Upload to experimental.

 -- Sebastian Dröge <slomo@debian.org>  Mon, 05 Apr 2021 11:13:34 +0300

gstreamer1.0 (1.18.3-1) unstable; urgency=medium

  * New upstream bugfix release.

 -- Sebastian Dröge <slomo@debian.org>  Thu, 14 Jan 2021 09:41:36 +0200

gstreamer1.0 (1.18.2-1) unstable; urgency=medium

  * New upstream bugfix release.

 -- Sebastian Dröge <slomo@debian.org>  Mon, 07 Dec 2020 10:00:44 +0200

"""
"""An example changelog snippet from gstreamer1.0"""
