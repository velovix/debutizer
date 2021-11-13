import os
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml
from xdg.BaseDirectory import save_config_path

from debutizer.errors import CommandError


class DebutizerYAMLError(CommandError):
    """An error as a result of the contents of the debutizer.yaml"""


class CredentialsYAMLError(CommandError):
    """An error as a result of the contents of the credentials.yaml"""


class S3RepoProfile:
    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        sign: bool = False,
        gpg_key_id: Optional[str] = None,
        cache_control: str = "public, max-age=3600",
        gpg_signing_key: Optional[str] = None,
        gpg_signing_password: Optional[str] = None,
    ):
        self.endpoint = endpoint
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.sign = sign
        self.gpg_key_id = gpg_key_id
        self.cache_control = cache_control
        self.gpg_signing_key = gpg_signing_key
        self.gpg_signing_password = gpg_signing_password

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "S3RepoProfile":
        endpoint = _required(config, "endpoint", str)
        bucket = _required(config, "bucket", str)
        sign = _optional(config, "sign", bool, False)
        gpg_key_id = _optional(config, "gpg_key_id", str, None)
        cache_control = _optional(config, "cache_control", str, "public, max-age=3600")

        credentials_file = _credentials_file()
        if credentials_file.is_file():
            credentials = yaml.load(credentials_file, yaml.Loader)
        else:
            credentials = None

        access_key = os.environ.get("DEBUTIZER_ACCESS_KEY")
        if access_key is None and credentials is not None:
            access_key = _optional(
                credentials, "access_key", str, None, error=CredentialsYAMLError
            )
        secret_key = os.environ.get("DEBUTIZER_SECRET_KEY")
        if secret_key is None and credentials is not None:
            secret_key = _optional(
                credentials, "secret_key", str, None, error=CredentialsYAMLError
            )

        gpg_signing_key = os.environ.get("DEBUTIZER_GPG_SIGNING_KEY")
        gpg_signing_password = os.environ.get("DEBUTIZER_GPG_SIGNING_PASSWORD")

        return S3RepoProfile(
            endpoint=endpoint,
            bucket=bucket,
            access_key=access_key,
            secret_key=secret_key,
            sign=sign,
            gpg_key_id=gpg_key_id,
            cache_control=cache_control,
            gpg_signing_key=gpg_signing_key,
            gpg_signing_password=gpg_signing_password,
        )

    def check_validity(self):
        if self.access_key is None or self.secret_key is None:
            raise CredentialsYAMLError(
                f"When using an S3-compatible bucket, an access key and secret key "
                f"must be provided so that Debutizer can authenticate against the "
                f"bucket. This can be done either through the DEBUTIZER_ACCESS_KEY and "
                f"DEBUTIZER_SECRET_KEY environment variables or in the "
                f"{_credentials_file()} file"
            )

        if self.sign and self.gpg_key_id is None and self.gpg_signing_key is None:
            raise DebutizerYAMLError(
                "When package signing is enabled, either the gpg_key_id field or "
                "DEBUTIZER_GPG_SIGNING_KEY environment variable must be set"
            )


class S3RepoConfiguration:
    def __init__(self, profiles: Dict[str, S3RepoProfile]):
        self.profiles = profiles

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "S3RepoConfiguration":
        profiles = {}

        for profile_name, profile_config in config.items():
            if not isinstance(profile_config, dict):
                raise DebutizerYAMLError(
                    f"Profile {profile_name} must be an object, got type "
                    f"{type(profile_config)}"
                )

            try:
                profiles[profile_name] = S3RepoProfile.from_dict(profile_config)
            except DebutizerYAMLError as ex:
                raise DebutizerYAMLError(f"For S3 repo profile {profile_name}: {ex}")

        return S3RepoConfiguration(profiles=profiles)

    def check_validity(self) -> None:
        for profile in self.profiles.values():
            profile.check_validity()


class PackageSource:
    def __init__(self, entry: str, gpg_key_url: Optional[str] = None):
        self.entry = entry
        self.gpg_key_url = gpg_key_url

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "PackageSource":
        return PackageSource(
            entry=_required(config, "entry", str),
            gpg_key_url=_optional(config, "gpg_key_url", str, None),
        )


class Configuration:
    def __init__(
        self,
        distributions: List[str],
        architectures: List[str],
        package_sources: List[PackageSource],
        upstream_repo: Optional[str] = None,
        upstream_is_trusted: bool = False,
        upstream_components: Optional[List[str]] = None,
        s3_repo: Optional[S3RepoConfiguration] = None,
    ):
        self.distributions = distributions
        self.architectures = architectures
        self.package_sources = package_sources
        self.upstream_repo = upstream_repo
        self.upstream_is_trusted = upstream_is_trusted
        self.upstream_components = upstream_components
        self.s3_repo = s3_repo

    @staticmethod
    def from_file(config_file: Path) -> "Configuration":
        with config_file.open("r") as f:
            config = yaml.load(f, yaml.Loader)

        try:
            distributions = _required(config, "distributions", list)
            architectures = _optional(
                config, "architecture", list, [_host_architecture()]
            )
            upstream_repo = _optional(config, "upstream_repo", str, None)
            upstream_is_trusted = _optional(config, "upstream_is_trusted", bool, False)
            upstream_components = _optional(config, "upstream_components", list, None)

            package_sources = []
            package_source_dicts = _optional(config, "package_sources", list, [])
            for package_source_dict in package_source_dicts:
                package_sources.append(PackageSource.from_dict(package_source_dict))
        except DebutizerYAMLError as ex:
            raise CommandError(f"In {config_file}: {ex}")

        s3_repo_config = config.get("s3_repo")
        if s3_repo_config is None:
            s3_repo = None
        else:
            try:
                s3_repo = S3RepoConfiguration.from_dict(s3_repo_config)
            except DebutizerYAMLError as ex:
                raise CommandError(f"In {config_file}, in the s3_repo object: {ex}")

        return Configuration(
            distributions=distributions,
            architectures=architectures,
            package_sources=package_sources,
            upstream_repo=upstream_repo,
            upstream_is_trusted=upstream_is_trusted,
            upstream_components=upstream_components,
            s3_repo=s3_repo,
        )

    def check_validity(self):
        if self.upstream_repo is not None and self.upstream_components is None:
            raise DebutizerYAMLError(
                "If the upstream_repo field is set, the upstream_components field must "
                "be set as well"
            )


def _required(
    config: Dict[str, Any],
    key: str,
    type_: Type,
    error: Type[Exception] = DebutizerYAMLError,
) -> Any:
    try:
        value = config[key]
    except KeyError:
        raise error(f"Missing required field '{key}'")

    _check_type(key, value, type_, error)

    return value


def _optional(
    config: Dict[str, Any],
    key: str,
    type_: Type,
    default: Any,
    error: Type[Exception] = DebutizerYAMLError,
) -> Any:
    try:
        value = config[key]
    except KeyError:
        return default

    _check_type(key, value, type_, error)

    return value


def _check_type(key: str, value: Any, type_: Type, error: Type[Exception]) -> None:
    if not isinstance(value, type_):
        raise error(f"Field '{key}' is of type {type(value)}, but must be {type_}")


def _credentials_file() -> Path:
    return Path(save_config_path("debutizer")) / "s3-repo" / "credentials.yaml"


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
