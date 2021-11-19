import argparse
import sys
from typing import cast

from debutizer.commands import Command
from debutizer.commands.config_file import PPAConfiguration, S3Configuration
from debutizer.commands.env_argparse import EnvArgumentParser
from debutizer.commands.upload_targets import (
    PPAUploadTarget,
    S3UploadTarget,
    UploadTarget,
)
from debutizer.errors import CommandError
from debutizer.print_utils import print_color, print_done


class UploadCommand(Command):
    """Uploads packages to the configured target"""

    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer upload",
            description="Uploads packages to the configured target",
        )

        self.add_artifacts_dir_flag()
        self.add_config_file_flag()

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[2:])

    def behavior(self, args: argparse.Namespace) -> None:
        config = self.parse_config_file(args)
        if config.upload_target is None:
            raise CommandError(
                "The configuration file must have an upload target object"
            )
        config.upload_target.check_validity()

        upload_target: UploadTarget
        if config.upload_target.type == PPAConfiguration.TYPE:
            ppa_config = cast(PPAConfiguration, config.upload_target)
            upload_target = PPAUploadTarget(ppa_config)
        elif config.upload_target.type == S3Configuration.TYPE:
            s3_config = cast(S3Configuration, config.upload_target)
            upload_target = S3UploadTarget(s3_config)
        else:
            raise CommandError(
                f"Unknown upload target type '{config.upload_target.type}'"
            )

        upload_target.upload(args.artifacts_dir)

        print_color("")
        print_done("Upload complete!")
