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
