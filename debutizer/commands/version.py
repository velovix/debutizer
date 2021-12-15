import argparse

import pkg_resources

from debutizer.commands import Command
from debutizer.commands.env_argparse import EnvArgumentParser


class VersionCommand(Command):
    def __init__(self) -> None:
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer version",
            description="Prints the current version of Debutizer",
        )

    def behavior(self, args: argparse.Namespace) -> None:
        debutizer = pkg_resources.get_distribution("debutizer")
        print(debutizer.version)
