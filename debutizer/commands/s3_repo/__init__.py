import argparse
import sys

from debutizer.errors import CommandError

from ..command import Command
from ..env_argparse import EnvArgumentParser
from .upload import UploadCommand


class S3RepoCommand(Command):
    def __init__(self):
        self.parser = EnvArgumentParser(
            prog="debutizer s3-repo",
            description="Manages repositories backed by an S3-compatible bucket",
        )

        self.parser.add_argument("command", nargs="?", help="The command to run")

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[2:3])

    def behavior(self, args: argparse.Namespace) -> None:
        if args.command is None:
            self.parser.print_usage()
        elif args.command in S3RepoCommand.subcommands:
            command = S3RepoCommand.subcommands[args.command]
            command.run()
        else:
            raise CommandError(f"Unknown subcommand: {args.command}")
