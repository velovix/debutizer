from pathlib import Path
from typing import List, Optional, Union

from ...errors import CommandError
from ...print_utils import print_color
from ...subprocess_utils import run
from ..artifacts import (
    DEBIAN_SOURCE_FILE_GLOB,
    find_changes_files,
    find_debian_source_files,
)
from ..config_file import PPAConfiguration
from ..utils import configure_gpg, import_gpg_key
from .abstract import UploadTarget


class PPAUploadTarget(UploadTarget):
    """Uploads source packages to a PPA"""

    def __init__(self, ppa_config: PPAConfiguration):
        self._config = ppa_config

    def upload(self, artifacts_dir: Path) -> None:
        if self._config.gpg_signing_key is not None:
            import_gpg_key(self._config.gpg_signing_key)

        changes_files = find_changes_files(artifacts_dir, recursive=True)

        for changes_file in changes_files:
            if self._config.sign:
                dsc_files = find_debian_source_files(changes_file.parent)
                if len(dsc_files) == 0:
                    raise CommandError(
                        f"Changes file {changes_file} does not have a corresponding "
                        f"Debian source ({DEBIAN_SOURCE_FILE_GLOB}) file"
                    )
                dsc_file = dsc_files[0]

                print_color(f"Signing {changes_file} and {dsc_file}...")

                _debsign_file(
                    changes_file,
                    self._config.gpg_key_id,
                    self._config.gpg_signing_password,
                )

            print_color(f"Uploading {changes_file}...")
            dput_command: List[Union[Path, str]] = ["dput"]
            if self._config.force:
                dput_command.append("--force")
            dput_command += [self._config.repo, changes_file]
            run(
                command=dput_command,
                on_failure="Failed to upload the changes file to the PPA",
            )


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
