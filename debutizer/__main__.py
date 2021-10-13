import argparse
import os
import sys

from debutizer.commands import commands
from debutizer.errors import CommandError
from debutizer.print_utils import Color, Format, print_color


def main():
    """An exception handling wrapper around the real entrypoint, _main"""
    try:
        _main()
    except CommandError as ex:
        print("")
        print_color(ex.message, color=Color.RED, format_=Format.BOLD, file=sys.stderr)
        if "DEBUTIZER_SHOW_TRACEBACKS" in os.environ:
            raise ex
        else:
            sys.exit(1)


def _main():
    args = _parse_args()

    if args.command is None:
        print(
            "Debutizer is a tool for managing APT packages.\n\n"
            "To get started, try running 'debutizer --help'."
        )
    elif args.command in commands:
        command = commands[args.command]
        command.run()
    else:
        raise CommandError(f"Unknown command: {args.command}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="debutizer",
        description="A tool for managing APT packages",
    )

    parser.add_argument("command", nargs="?", help="The command to run")

    return parser.parse_args(sys.argv[1:2])


if __name__ == "__main__":
    main()
