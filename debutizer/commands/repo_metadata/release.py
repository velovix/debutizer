import os
import subprocess
from contextlib import ExitStack
from pathlib import Path
from typing import Dict, List, Optional, Union

from debutizer.commands.utils import temp_file
from debutizer.errors import CommandError
from debutizer.print_utils import Color, Format, print_color
from debutizer.subprocess_utils import run


def add_release_files(
    artifacts_dir: Path, sign: bool, gpg_key_id: Optional[str]
) -> List[Path]:
    """Adds Release files to the given APT package file tree. Release files provide MD5
    hashes for Packages and Sources files, verifying their integrity. They also contain
    metadata related to the repository.

    If the sign argument is set to True, an InRelease file will be created alongside
    each Release file. This is a GPG-signed version of the Release file, used to further
    verify file integrity.

    One Release file is made per distribution, and they are placed in
    "dists/{distro}/Release".

    :param artifacts_dir: The root of the APT package file tree
    :param sign: If true, Release files will be signed as InRelease files
    :param gpg_key_id: If provided, the GPG key with this ID will be used to sign
    :return: The newly created Release (and potentially InRelease) files
    """
    release_files = []

    if sign and gpg_key_id is None:
        _import_gpg_key(os.environ["GPG_SIGNING_KEY"])

    dirs = artifacts_dir.glob("dists/*")
    dirs = (d.relative_to(artifacts_dir) for d in dirs)

    for dir_ in dirs:
        print_color(
            f"Updating the Release file for {dir_}",
            color=Color.MAGENTA,
            format_=Format.BOLD,
        )

        metadata = _repo_metadata(artifacts_dir / dir_)
        metadata_flags = []
        for key, value in metadata.items():
            metadata_flags += ["-o", f"APT::FTPArchive::Release::{key}={value}"]

        result = run(
            [
                "apt-ftparchive",
                "release",
                *metadata_flags,
                dir_,
            ],
            on_failure="Failed to update the Release file",
            cwd=artifacts_dir,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        release_file = artifacts_dir / dir_ / "Release"
        release_content = result.stdout.encode()
        release_file.write_bytes(release_content)
        release_files.append(release_file)

        if sign:
            print_color(
                f"Signing the Release file for {dir_}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

            signed_release_file = release_file.with_name("InRelease")
            _sign_file(release_file, signed_release_file, gpg_key_id)
            release_files.append(signed_release_file)

    return release_files


def _import_gpg_key(key: str) -> None:
    process = subprocess.Popen(
        [
            "gpg",
            "--armor",
            "--import",
            "--no-tty",
            "--batch",
            "--yes",
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    process.communicate(input=key.encode())
    if process.returncode != 0:
        raise CommandError("Failed to import the GPG key")


def _sign_file(input_: Path, output: Path, gpg_key_id: Optional[str]) -> None:
    command: List[Union[str, Path]] = [
        "gpg",
        "--pinentry-mode=loopback",
        "--batch",
        "--yes",
        "--clear-sign",
        "--output",
        output,
    ]

    if gpg_key_id is not None:
        command += ["--default-key", gpg_key_id]

    gpg_password = os.environ.get("GPG_PASSWORD")

    with ExitStack() as stack:
        if gpg_password is not None:
            # Add a password if the GPG key uses one
            password_path = stack.enter_context(temp_file(gpg_password))
            command += ["--passphrase-file", password_path]

        # Add the actual GPG command, which must be after all options
        command += ["--sign", input_]

        run(command, on_failure=f"Failed to sign {input_} as {output}")


def _repo_metadata(path: Path) -> Dict[str, str]:
    metadata = {}

    # Extract the distribution codename from the path
    distribution = path.name

    # Extract supported components based on directories under dists/{distro}
    components = [c.name for c in path.iterdir() if c.is_dir()]

    # Extract supported architectures based on binary package directories under
    # dists/{distro}/{component}
    architectures = []
    for component in components:
        binary_paths = (path / component).glob("binary-*")
        component_architectures = [p.name.replace("binary-", "") for p in binary_paths]
        architectures += component_architectures

    metadata["Suite"] = distribution
    metadata["Codename"] = distribution
    metadata["Components"] = " ".join(components)
    metadata["Architectures"] = " ".join(architectures)
    # TODO: Make this configurable
    metadata["Label"] = "Made with Debutizer"

    return metadata
