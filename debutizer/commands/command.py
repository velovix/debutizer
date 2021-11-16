import argparse
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List

from debutizer.print_utils import print_warning

from ..errors import CommandError
from .config_file import Configuration
from .env_argparse import EnvArgumentParser


class Command(ABC):
    """A Debutizer CLI command"""

    parser: EnvArgumentParser
    subcommands: Dict[str, "Command"]
    cleanup_hooks: List[Callable[[], None]]
    """Hooks that run after a command is finished, even in the case of an error"""

    def __init__(self):
        self.subcommands = {}
        self.cleanup_hooks = []

    def add_subcommand(self, name: str, command: "Command") -> None:
        """Registers the command under the given name.

        :param name: The name of the command
        :param command: The command to register
        """
        self.subcommands[name] = command

    @abstractmethod
    def behavior(self, args: argparse.Namespace) -> None:
        """Behavior for when the command is run"""

    def clean_up(self) -> None:
        """Runs any clean-up hooks"""
        try:
            for hook in self.cleanup_hooks:
                hook()
        except Exception as ex:
            print_warning(f"WARNING: Ignoring exception while cleaning up: {ex}")

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[2:])

    def parse_config_file(self, args: argparse.Namespace) -> Configuration:
        if not args.config_file.is_file():
            raise CommandError(f"Configuration file '{args.config_file}' not found")

        return Configuration.from_file(args.config_file)

    def run(self) -> None:
        """Runs the command"""
        args = self.parse_args()
        try:
            self.behavior(args)
        finally:
            self.clean_up()

    def add_artifacts_dir_flag(self) -> None:
        self.parser.add_env_flag(
            "--artifacts-dir",
            type=Path,
            default=Path.cwd() / "artifacts",
            required=False,
            help="The directory that will hold the resulting packages and other "
            "artifacts",
        )

    def add_config_file_flag(self) -> None:
        self.parser.add_env_flag(
            "--config-file",
            type=Path,
            default="debutizer.yaml",
            required=False,
            help="The configuration file to reference",
        )

    def add_package_dir_flag(self) -> None:
        self.parser.add_env_flag(
            "--package-dir",
            type=Path,
            default=Path.cwd() / "packages",
            required=False,
            help="The directory that holds the package directories",
        )
