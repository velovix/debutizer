import os
import sys

from debutizer import commands
from debutizer.errors import CommandError
from debutizer.print_utils import Color, Format, print_color


def main():
    """An exception handling wrapper around the real entrypoint, _main"""
    try:
        _main()
    except (CommandError, KeyboardInterrupt) as ex:
        print("")
        if isinstance(ex, KeyboardInterrupt):
            print_color(
                "Interrupted by SIGINT",
                color=Color.RED,
                format_=Format.BOLD,
                file=sys.stderr,
            )
        else:
            print_color(
                ex.message, color=Color.RED, format_=Format.BOLD, file=sys.stderr
            )
        if "DEBUTIZER_SHOW_TRACEBACKS" in os.environ:
            raise ex
        else:
            sys.exit(1)


def _main():
    root = commands.RootCommand()

    root.add_subcommand("source", commands.SourceCommand())
    root.add_subcommand("build", commands.BuildCommand())

    s3_repo_command = commands.S3RepoCommand()
    root.add_subcommand("s3-repo", s3_repo_command)
    s3_repo_command.add_subcommand("upload", commands.s3_repo.UploadCommand())

    root.run()


if __name__ == "__main__":
    main()
