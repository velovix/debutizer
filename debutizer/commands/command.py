import argparse
import os
import platform
import sys
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Type

from xdg import xdg_cache_home

from ..errors import CommandError


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

    def add_common_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--package-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_PACKAGE_DIR", Path.cwd() / "packages"),
            required=False,
            help="The directory that holds the package directories",
        )

        default_build_dir = xdg_cache_home() / "debutizer"
        parser.add_argument(
            "--build-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_BUILD_DIR", default_build_dir),
            required=False,
            help="The directory that will hold intermediate build files",
        )

        parser.add_argument(
            "--artifacts-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_ARTIFACTS_DIR", Path.cwd() / "artifacts"),
            required=False,
            help="The directory that will hold the resulting packages and other "
            "artifacts",
        )

        parser.add_argument(
            "--distribution",
            type=str,
            required=True,
            help="The codename of the distribution to build packages against, like "
            "'focal' or 'sid'.",
        )

        # TODO: Update the help text when cross-building is supported. qemubuilder?
        parser.add_argument(
            "--architecture",
            type=str,
            required=False,
            default=_host_architecture(),
            help="The architecture to build packages against, like 'amd64' or 'arm64'. "
            "Defaults to the host architecture. Changing this value will currently "
            "break your build.",
        )


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


def _host_architecture() -> str:
    """
    :return: Debian's name for the host CPU architecture
    """
    arch = platform.machine()

    # Python uses the GNU names for architectures, which is sometimes different from
    # Debian's names. This is documented in /usr/share/dpkg/cputable.
    if arch == "x86_64":
        return "amd64"
    elif arch == "aarch64":
        return "amd64"
    else:
        return arch
