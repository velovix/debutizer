import argparse
import shutil

from ..errors import CommandError
from ..print_utils import Color, Format, print_color, print_done
from .command import Command
from .env_argparse import EnvArgumentParser


class CheckCommand(Command):
    """Checks if all of Debutizer's system dependencies are available"""

    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer check",
            description="Checks if all required system dependencies are provided",
        )

    def behavior(self, args: argparse.Namespace) -> None:
        max_name_length = 0
        for package_name in _DEPENDENCIES.keys():
            if len(package_name) > max_name_length:
                max_name_length = len(package_name)

        success = True

        for package_name, commands in _DEPENDENCIES.items():
            message = "Installed!"
            found = True
            for command in commands:
                if not shutil.which(command):
                    message = f"Missing! Command not found: {command}"
                    found = False
                    success = False

            package_name = f"{package_name}:".ljust(max_name_length + 8)
            print_color(
                package_name,
                color=Color.MAGENTA,
                format_=Format.BOLD,
                end="",
            )
            print_color(
                message,
                color=Color.GREEN if found else Color.RED,
                format_=Format.BOLD,
            )

        if success:
            print_color("")
            print_done(
                "All system dependencies are available! You should be good to go."
            )
        else:
            raise CommandError("Some dependencies could not be found")


_DEPENDENCIES = {
    "dpkg-dev": ["dpkg-scanpackages", "dpkg-scansources", "dpkg-genchanges"],
    "gpg": ["gpg"],
    "apt-utils": ["apt-ftparchive"],
    "quilt": ["quilt"],
    "pbuilder": ["pbuilder"],
    "s3fs": ["s3fs"],
    "devscripts": ["dget"],
    "git": ["git"],
}
"""System dependencies, where the key is the Debian package name and the value is a list
of expected commands from that package
"""
