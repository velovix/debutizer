import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

from debutizer.commands.utils import configure_gpg, import_gpg_key
from debutizer.print_utils import print_notify
from debutizer.subprocess_utils import run


def add_release_files(
    artifacts_dir: Path,
    sign: bool,
    gpg_key_id: Optional[str],
    gpg_signing_key: Optional[str],
    gpg_signing_password: Optional[str],
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
    :param gpg_signing_key: If provided the GPG key in this string will be imported and
        used
    :param gpg_signing_password: The password for the GPG signing key, if one is
        necessary
    :return: The newly created Release (and potentially InRelease) files
    """
    release_files = []

    if sign and gpg_signing_key is not None:
        import_gpg_key(gpg_signing_key)

    dirs = artifacts_dir.glob("dists/*")
    dirs = (d.relative_to(artifacts_dir) for d in dirs)

    for dir_ in dirs:
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
            print_notify(f"Signing the Release file for {dir_}")

            signed_release_file = release_file.with_name("InRelease")
            _sign_file(
                release_file, signed_release_file, gpg_key_id, gpg_signing_password
            )
            release_files.append(signed_release_file)

    return release_files


def _sign_file(
    input_: Path,
    output: Path,
    gpg_key_id: Optional[str],
    gpg_signing_password: Optional[str],
) -> None:
    with configure_gpg(gpg_key_id, gpg_signing_password) as configuration:
        command: List[Union[str, Path]] = []
        command += configuration

        command += ["--clear-sign"]
        command += ["--output", output]
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
