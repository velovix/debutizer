import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List

from .errors import CommandError
from .print_utils import Color, Format, print_color


def run(
    command: List[str],
    *,
    on_failure: str,
    cwd: Path = Path.cwd(),
    env: Dict[str, str] = None,
    root: bool = False,
):
    if root and os.geteuid() != 0:
        # Use a command (probably sudo) to get root permissions
        root_command_str = os.environ.get("DEBUTIZER_ROOT_COMMAND", "sudo -E")
        root_command = shlex.split(root_command_str)
        command = root_command + command

    command_str = " ".join(command)
    print_color(f"> {command_str}", format_=Format.BOLD)

    try:
        subprocess.run(command, check=True, cwd=cwd, env=env)
    except subprocess.CalledProcessError as ex:
        raise CommandError(on_failure) from ex
