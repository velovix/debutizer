from enum import Enum
from typing import List, Optional, Union

from debian.deb822 import Deb822

from .errors import CommandError, UnexpectedError


class ListType(Enum):
    """Debian files have a few ways of defining lists"""

    COMMAS = 1
    """A single line, with commas between elements"""
    COMMAS_MULTILINE = 2
    """A line per element, with a comma between elements. Usually (always?)
    syntactically the same as COMMAS, but looks better for long lists.
    """
    WHITESPACE_SEPARATED = 3
    """A single line, with spaces between elements"""
    LINE_BASED = 4
    """A line per element, with no other separator"""


def add_field(
    fields: Deb822,
    name: str,
    value: Optional[Union[str, List[str], bool]],
    list_type: ListType = ListType.COMMAS,
):
    if value is None:
        return

    if isinstance(value, str):
        value_str = value
    elif isinstance(value, list):
        if list_type is ListType.COMMAS:
            value_str = ", ".join(value)
        elif list_type is ListType.COMMAS_MULTILINE:
            value_str = ""
            for item in value:
                value_str += f"\n {item},"
        elif list_type is ListType.WHITESPACE_SEPARATED:
            value_str = " ".join(value)
        elif list_type is ListType.LINE_BASED:
            value_str = ""
            for item in value:
                value_str += f"\n {item}"
        else:
            raise UnexpectedError(f"Unknown ListType '{list_type}'.")
    elif isinstance(value, bool):
        value_str = "yes" if value else "no"
    else:
        raise CommandError(f"Invalid value type for field '{name}': {type(value)}")

    fields[name] = value_str
