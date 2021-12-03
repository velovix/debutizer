import argparse

from debutizer import __version__
from debutizer.commands import Command
from debutizer.commands.env_argparse import EnvArgumentParser


class VersionCommand(Command):
    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer version",
            description="Prints the current version of Debutizer",
        )

    def behavior(self, args: argparse.Namespace) -> None:
        print(__version__)
