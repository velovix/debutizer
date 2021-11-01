import argparse
import os
import platform
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List

from xdg.BaseDirectory import save_cache_path

from debutizer.print_utils import Color, Format, print_color


class Command(ABC):
    """A Debutizer CLI command"""

    parser: argparse.ArgumentParser
    subcommands: Dict[str, "Command"] = {}
    cleanup_hooks: List[Callable[[], None]] = []
    """Hooks that run after a command is finished, even in the case of an error"""

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
            print_color(
                f"WARNING: Ignoring exception while cleaning up: {ex}",
                color=Color.YELLOW,
                format_=Format.BOLD,
                file=sys.stderr,
            )

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[2:])

    def run(self) -> None:
        """Runs the command"""
        args = self.parse_args()
        try:
            self.behavior(args)
        finally:
            self.clean_up()

    def add_archive_args(self) -> None:
        self.parser.add_argument(
            "--artifacts-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_ARTIFACTS_DIR", Path.cwd() / "artifacts"),
            required=False,
            help="The directory that will hold the resulting packages and other "
            "artifacts",
        )

    def add_common_args(self) -> None:
        self.add_archive_args()

        self.parser.add_argument(
            "--package-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_PACKAGE_DIR", Path.cwd() / "packages"),
            required=False,
            help="The directory that holds the package directories",
        )

        default_build_dir = save_cache_path("debutizer")
        self.parser.add_argument(
            "--build-dir",
            type=Path,
            default=os.environ.get("DEBUTIZER_BUILD_DIR", default_build_dir),
            required=False,
            help="The directory that will hold intermediate build files",
        )

        self.parser.add_argument(
            "--distribution",
            type=str,
            required=True,
            help="The codename of the distribution to build packages against, like "
            "'focal' or 'sid'.",
        )

        # TODO: Update the help text when cross-building is supported. qemubuilder?
        self.parser.add_argument(
            "--architecture",
            type=str,
            required=False,
            default=_host_architecture(),
            help="The architecture to build packages against, like 'amd64' or 'arm64'. "
            "Defaults to the host architecture. Changing this value will currently "
            "break your build.",
        )


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
