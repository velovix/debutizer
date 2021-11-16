import os
import sys

from debutizer import commands
from debutizer.errors import CommandError
from debutizer.print_utils import print_color, print_error


def main():
    """An exception handling wrapper around the real entrypoint, _main"""
    try:
        _main()
    except (CommandError, KeyboardInterrupt) as ex:
        print_color("")
        if isinstance(ex, KeyboardInterrupt):
            print_error("Interrupted by SIGINT")
        else:
            print_error(ex.message)
        if "DEBUTIZER_SHOW_TRACEBACKS" in os.environ:
            raise ex
        else:
            sys.exit(1)


def _main():
    root = commands.RootCommand()

    root.add_subcommand("source", commands.SourceCommand())
    root.add_subcommand("build", commands.BuildCommand())
    root.add_subcommand("check", commands.CheckCommand())
    root.add_subcommand("upload", commands.UploadCommand())

    root.run()


if __name__ == "__main__":
    main()
