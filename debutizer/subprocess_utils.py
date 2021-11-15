import os
import shlex
import subprocess
from pathlib import Path
from typing import List, Union

from .errors import CommandError, UnexpectedError
from .print_utils import Format, print_color


def run(
    command: List[Union[str, Path]],
    *,
    on_failure: str,
    root: bool = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    for i, arg in enumerate(command):
        if not isinstance(arg, (str, Path)):
            raise UnexpectedError(
                f"Argument {i} is of type {type(arg)}, but must be a str or Path object"
            )
    command_no_path = [str(c) for c in command]

    if root and os.geteuid() != 0:
        if os.environ.get("DEBUTIZER_ACQUIRE_ROOT"):
            # Use a command (probably sudo) to get root permissions
            root_command_str = os.environ.get("DEBUTIZER_ROOT_COMMAND", "sudo -E")
            root_command = shlex.split(root_command_str)
            command_no_path = root_command + command_no_path
        else:
            raise CommandError(
                f"Command '{' '.join(command_no_path)}' must have root permissions"
            )

    # TODO: Use shlex.join when Python 3.8 is the oldest supported version
    command_str = " ".join(command_no_path)
    print_color(f"> {command_str}", format_=Format.BOLD)

    try:
        return subprocess.run(command_no_path, check=True, **kwargs)
    except subprocess.CalledProcessError as ex:
        raise CommandError(on_failure) from ex
