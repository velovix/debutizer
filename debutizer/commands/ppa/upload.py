import argparse
import sys
from pathlib import Path
from typing import List, Optional, Union

from debutizer.commands import Command
from debutizer.commands.artifacts import (
    DEBIAN_SOURCE_FILE_GLOB,
    find_changes_files,
    find_debian_source_files,
)
from debutizer.commands.env_argparse import EnvArgumentParser
from debutizer.commands.utils import configure_gpg, import_gpg_key
from debutizer.errors import CommandError
from debutizer.print_utils import print_color, print_done
from debutizer.subprocess_utils import run


class UploadCommand(Command):
    def __init__(self):
        self.parser = EnvArgumentParser(
            prog="debutizer ppa upload",
            description="Uploads source packages to a PPA",
        )

        self.add_artifacts_dir_flag()
        self.add_config_file_flag()
        self.add_profile_flag()

        self.parser.add_env_flag(
            "--force",
            action="store_true",
            help="If provided, packages will be uploaded even if it appears to have "
            "already been uploaded",
        )

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args(sys.argv[3:])

    def behavior(self, args: argparse.Namespace) -> None:
        config = self.parse_config_file(args)
        if config.ppa is None:
            raise CommandError("The configuration file must have a ppa object")
        config.check_validity()

        try:
            profile = config.ppa.profiles[args.profile]
        except KeyError:
            raise CommandError(
                f"Profile '{args.profile}' is not defined in {args.config_file}"
            )
        profile.check_validity()

        changes_files = find_changes_files(args.artifacts_dir, recursive=True)

        for changes_file in changes_files:
            if profile.sign:
                dsc_files = find_debian_source_files(changes_file.parent)
                if len(dsc_files) == 0:
                    raise CommandError(
                        f"Changes file {changes_file} does not have a corresponding "
                        f"Debian source ({DEBIAN_SOURCE_FILE_GLOB}) file"
                    )
                dsc_file = dsc_files[0]

                print_color(f"Signing {changes_file} and {dsc_file}...")
                if profile.gpg_key_id is None and profile.gpg_signing_key is not None:
                    import_gpg_key(profile.gpg_signing_key)

                _debsign_file(
                    changes_file,
                    profile.gpg_key_id,
                    profile.gpg_signing_password,
                )

            print_color(f"Uploading {changes_file}...")
            dput_command: List[Union[Path, str]] = ["dput"]
            if args.force:
                dput_command.append("--force")
            dput_command += [profile.repo, changes_file]
            run(
                command=dput_command,
                on_failure="Failed to upload the changes file to the PPA",
            )

        print_color("")
        print_done("Upload complete!")


def _debsign_file(
    input_: Path,
    gpg_key_id: Optional[str],
    gpg_signing_password: Optional[str],
) -> None:
    """Uses debsign to sign the given file using a GPG key"""
    with configure_gpg(gpg_key_id, gpg_signing_password) as command:
        command_str = " ".join(command)
        run(
            ["debsign", f"-p{command_str}", "--re-sign", input_],
            on_failure=f"Failed to sign {input_}",
        )
