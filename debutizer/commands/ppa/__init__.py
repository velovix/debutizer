import argparse
import sys

from debutizer.commands import Command
from debutizer.commands.env_argparse import EnvArgumentParser
from debutizer.errors import CommandError

from .upload import UploadCommand


class PPACommand(Command):
    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer ppa",
            description="Manages Ubuntu PPAs",
        )

        self.parser.add_argument("command", nargs="?", help="The command to run")

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[2:3])

    def behavior(self, args: argparse.Namespace) -> None:
        if args.command is None:
            self.parser.print_usage()
        elif args.command in self.subcommands:
            command = self.subcommands[args.command]
            command.run()
        else:
            raise CommandError(f"Unknown subcommand: {args.command}")
