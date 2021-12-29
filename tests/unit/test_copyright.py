from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from debian.deb822 import Deb822

from debutizer._license_full_text import spdx_to_full_text
from debutizer.copyright import Copyright


@pytest.mark.parametrize("spdx_identifier", spdx_to_full_text.keys())
def test_license_full_text_formatting(spdx_identifier: str):
    """Tests that the Deb822 object's formatting checks pass for every piece of full
    license text.
    """
    deb822 = Deb822()
    deb822["License"] = Copyright.full_license_text(spdx_identifier)


def test_copyright_retains_everything():
    """Tests that, after being parsed and dumped back to the file system, all data and
    formatting on the copyright is retained
    """
    with _package_dir() as package_dir:
        copyright_file = package_dir / Copyright.FILE_PATH

        copyright_ = Copyright(package_dir)

        copyright_.load()
        copyright_.save()

        assert copyright_file.read_text() == _COPYRIGHT_STR


@contextmanager
def _package_dir():
    """Creates a temporary directory with an example copyright file inside it"""

    with TemporaryDirectory() as dir_str:
        dir_ = Path(dir_str)
        dir_.mkdir(exist_ok=True)
        changelog_file = dir_ / Copyright.FILE_PATH
        changelog_file.parent.mkdir(exist_ok=True)
        changelog_file.write_text(_COPYRIGHT_STR)

        yield dir_


_COPYRIGHT_STR = """Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: GStreamer core 1.0
Upstream-Contact:
 gstreamer-devel@lists.freedesktop.org
Source: http://gstreamer.freedesktop.org

Files: gst/gst.c gst/gst.h gst/gst_private.h
Copyright: 1999-2000, Erik Walthinsen <omega@cse.ogi.edu>
License: LGPL-2+

Files: libs/gst/check/libcheck/check.c
Copyright: 2001, 2002, Arien Malec
  2001-2002, Arien Malec
License: LGPL-2.1+

License: LGPL-2.1+
  This package is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2 of the License, or (at your option) any later version.
  .
  This package is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.
  .
  You should have received a copy of the GNU Lesser General Public
  License along with this package; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
  .
  On Debian GNU/Linux systems, the complete text of the GNU Lesser General
  Public License can be found in `/usr/share/common-licenses/LGPL'.
"""
