import argparse
import sys

from debutizer.commands import commands
from debutizer.errors import CommandError
from debutizer.translate import make_translator

tr = make_translator("portal")


def main():
    args = _parse_args()

    if args.command is None:
        print(tr("introduction"))
    elif args.command in commands:
        command = commands[args.command]
        command.run()
    else:
        error = tr("unknown-command").format(command=args.command)
        raise CommandError(error)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="debutizer",
        description=tr("description"),
    )

    parser.add_argument("command", nargs="?", help=tr("command-help"))

    return parser.parse_args(sys.argv[1:2])


if __name__ == "__main__":
    try:
        main()
    except CommandError as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)
