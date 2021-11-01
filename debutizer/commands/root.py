import argparse
import sys

from ..errors import CommandError
from .command import Command


class RootCommand(Command):
    """The command at the root of the command tree. All top-level commands, like
    'debutizer build', are a subcommand of this command.
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="debutizer",
            description="A tool for managing APT packages",
        )

        self.parser.add_argument("command", nargs="?", help="The command to run")

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[1:2])

    def behavior(self, args: argparse.Namespace) -> None:
        if args.command is None:
            print(
                "Debutizer is a tool for managing APT packages.\n\n"
                "To get started, try running 'debutizer --help'."
            )
        elif args.command in self.subcommands:
            command = self.subcommands[args.command]
            command.run()
        else:
            raise CommandError(f"Unknown command: {args.command}")
