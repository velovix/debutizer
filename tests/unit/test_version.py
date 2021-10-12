import pytest

from debutizer.errors import CommandError
from debutizer.version import Version


@pytest.mark.parametrize(
    "input_,expected",
    [
        (
            "1.4.3-1",
            Version(
                epoch=None,
                upstream_version="1.4.3",
                debian_revision="1",
                full_version="1.4.3-1",
            ),
        ),
        (
            "3.7-myorg0.1",
            Version(
                epoch=None,
                upstream_version="3.7",
                debian_revision="myorg0.1",
                full_version="3.7-myorg0.1",
            ),
        ),
        (
            "7:3.4.8-0ubuntu0.2",
            Version(
                epoch="7",
                upstream_version="3.4.8",
                debian_revision="0ubuntu0.2",
                full_version="7:3.4.8-0ubuntu0.2",
            ),
        ),
    ],
)
def test_valid_version_parsing(input_: str, expected: Version) -> None:
    actual = Version.from_string(input_)
    assert actual == expected


@pytest.mark.parametrize(
    "input_", ["1.4.3", "epochonly:", "5:4.9.2", ":8.7.2", "-revisiononly"]
)
def test_invalid_version_parsing(input_: str) -> None:
    with pytest.raises(CommandError):
        Version.from_string(input_)
