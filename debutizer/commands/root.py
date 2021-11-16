import argparse
import sys

from ..errors import CommandError
from ..print_utils import print_color
from .command import Command
from .env_argparse import EnvArgumentParser


class RootCommand(Command):
    """The command at the root of the command tree. All top-level commands, like
    'debutizer build', are a subcommand of this command.
    """

    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer",
            description="A tool for managing APT packages",
            usage=_USAGE,
        )

        self.parser.add_argument("command", nargs="?", help="The command to run")

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[1:2])

    def behavior(self, args: argparse.Namespace) -> None:
        if args.command is None:
            print_color(
                "Debutizer is a tool for managing APT packages.\n\n"
                "To get started, try running 'debutizer --help'."
            )
        elif args.command in self.subcommands:
            command = self.subcommands[args.command]
            command.run()
        else:
            raise CommandError(f"Unknown command: {args.command}")


_USAGE = """debutizer <command> [<args>]

Commands:
  source    Makes source packages
  build     Makes source and binary packages
  check     Checks for system dependencies
  upload    Uploads packages
"""
