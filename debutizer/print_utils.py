import os
import sys
from enum import Enum


class Color(Enum):
    """ANSI escape codes representing colors in the terminal theme."""

    WHITE = ""
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


class Format(Enum):
    """ANSI escape codes telling the terminal to use special formatting for the text"""

    NORMAL = ""
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_color(
    message: str,
    color: Color = Color.WHITE,
    format_: Format = Format.NORMAL,
    file=sys.stderr,
    **kwargs,
) -> None:
    color = _check_no_color(color)
    format_ = _check_no_formatting(format_)
    print(f"{format_.value}{color.value}{message}{_END}", file=file, **kwargs)


def print_done(task: str):
    if "DEBUTIZER_AVRDUDE_MODE" in os.environ:
        message = "debutizer done.  Thank you."
    else:
        message = f"{task} complete!"

    print_color(message, color=Color.GREEN, format_=Format.BOLD)


def _check_no_color(color: Color) -> Color:
    """Turns off color if the user wants.
    See: https://no-color.org/
    """
    if "NO_COLOR" in os.environ:
        return Color.WHITE
    return color


def _check_no_formatting(format_: Format) -> Format:
    """Turns off formatting if the user wants.
    See: https://no-color.org/
    """
    if "NO_COLOR" in os.environ:
        return Format.NORMAL
    return format_


# Terminates any previous formatting escape codes
_END = "\033[0m"
