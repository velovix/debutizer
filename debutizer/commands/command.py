import argparse
import sys
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Dict, Type


class Command(ABC):
    @abstractmethod
    def define_args(self) -> argparse.ArgumentParser:
        """Defines the arguments that the command will take"""

    @abstractmethod
    def behavior(self, args: argparse.Namespace) -> None:
        """Behavior for when the command is run"""

    def run(self) -> None:
        """Runs the command"""
        parser = self.define_args()
        args = parser.parse_args(sys.argv[2:])
        self.behavior(args)


commands: Dict[str, Command] = {}


def register(name: str) -> Callable[[Type], Any]:
    """Registers the command under the given name.

    :param name: The name of the command
    """

    def decorator(cls):
        commands[name] = cls()

        @wraps(cls)
        def wrapper(*args, **kwargs):
            return cls(*args, **kwargs)

        return wrapper

    return decorator
