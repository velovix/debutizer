import os
import platform
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml
from xdg.BaseDirectory import save_config_path

from debutizer.errors import CommandError


class DebutizerYAMLError(CommandError):
    """An error as a result of the contents of the debutizer.yaml"""


class CredentialsYAMLError(CommandError):
    """An error as a result of the contents of the credentials.yaml"""


class _ConfigurationSection(ABC):
    """A YAML object within the debutizer.yaml"""

    @staticmethod
    @abstractmethod
    def from_dict(config: Dict[str, Any]):
        ...


class UploadTargetConfiguration(_ConfigurationSection):
    def __init__(self, type_: str):
        self.type = type_

    @abstractmethod
    def check_validity(self):
        ...


class S3Configuration(UploadTargetConfiguration):
    TYPE = "s3"

    def __init__(
        self,
        endpoint: str,
        bucket: str,
        prefix: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        sign: bool = False,
        gpg_key_id: Optional[str] = None,
        cache_control: str = "public, max-age=3600",
        gpg_signing_key: Optional[str] = None,
        gpg_signing_password: Optional[str] = None,
    ):
        super().__init__(S3Configuration.TYPE)

        if prefix is not None:
            # Normalize slashes in prefix
            if prefix.startswith("/"):
                prefix = prefix[1:]
            if prefix.endswith("/"):
                prefix = prefix[:-1]

        self.endpoint = endpoint
        self.bucket = bucket
        self.prefix = prefix
        self.access_key = access_key
        self.secret_key = secret_key
        self.sign = sign
        self.gpg_key_id = gpg_key_id
        self.cache_control = cache_control
        self.gpg_signing_key = gpg_signing_key
        self.gpg_signing_password = gpg_signing_password

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "S3Configuration":
        endpoint = _required(config, "endpoint", str)
        bucket = _required(config, "bucket", str)
        prefix = _optional(config, "prefix", str, None)
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

        return S3Configuration(
            endpoint=endpoint,
            bucket=bucket,
            prefix=prefix,
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

        if self.sign and self.gpg_key_id is None:
            raise DebutizerYAMLError(
                "When package signing is enabled, the gpg_key_id field must be set"
            )


class PPAConfiguration(UploadTargetConfiguration):
    TYPE = "ppa"

    def __init__(
        self,
        repo: str,
        sign: bool = True,
        gpg_key_id: Optional[str] = None,
        gpg_signing_key: Optional[str] = None,
        gpg_signing_password: Optional[str] = None,
        force: Optional[bool] = False,
    ):
        super().__init__(PPAConfiguration.TYPE)

        self.repo = repo
        self.sign = sign
        self.gpg_key_id = gpg_key_id
        self.gpg_signing_key = gpg_signing_key
        self.gpg_signing_password = gpg_signing_password
        self.force = force

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "PPAConfiguration":
        gpg_signing_key = os.environ.get("DEBUTIZER_GPG_SIGNING_KEY")
        gpg_signing_password = os.environ.get("DEBUTIZER_GPG_SIGNING_PASSWORD")

        return PPAConfiguration(
            repo=_required(config, "repo", str),
            sign=_optional(config, "sign", bool, True),
            gpg_key_id=_optional(config, "gpg_key_id", str, None),
            gpg_signing_key=gpg_signing_key,
            gpg_signing_password=gpg_signing_password,
            force=_optional(config, "force", bool, False),
        )

    def check_validity(self):
        if self.sign and self.gpg_key_id is None:
            raise DebutizerYAMLError(
                "When package signing is enabled, the gpg_key_id field must be set"
            )


class PackageSource(_ConfigurationSection):
    def __init__(self, entry: str, gpg_key_url: Optional[str] = None):
        self.entry = entry
        self.gpg_key_url = gpg_key_url

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "PackageSource":
        return PackageSource(
            entry=_required(config, "entry", str),
            gpg_key_url=_optional(config, "gpg_key_url", str, None),
        )


class UpstreamConfiguration(_ConfigurationSection):
    def __init__(
        self,
        url: str,
        components: List[str],
        is_trusted: Optional[bool] = False,
        gpg_key_url: Optional[str] = None,
    ):
        self.url = url
        self.components = components
        self.is_trusted = is_trusted
        self.gpg_key_url = gpg_key_url

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "UpstreamConfiguration":
        return UpstreamConfiguration(
            url=_required(config, "url", str),
            components=_optional(config, "components", list, ["main"]),
            is_trusted=_optional(config, "is_trusted", bool, False),
            gpg_key_url=_optional(config, "gpg_key_url", str, None),
        )


class Configuration:
    def __init__(
        self,
        distributions: List[str],
        architectures: List[str],
        package_sources: List[PackageSource],
        upstream: Optional[UpstreamConfiguration] = None,
        upload_target: Optional[UploadTargetConfiguration] = None,
    ):
        self.distributions = distributions
        self.architectures = architectures
        self.package_sources = package_sources
        self.upstream = upstream
        self.upload_target = upload_target

    @staticmethod
    def from_file(config_file: Path) -> "Configuration":
        with config_file.open("r") as f:
            config = yaml.load(f, yaml.Loader)

        try:
            distributions = _required(config, "distributions", list)
            architectures = _optional(
                config, "architecture", list, [_host_architecture()]
            )

            upstream = None
            upstream_config = _optional(config, "upstream", dict, None)
            if upstream_config is not None:
                upstream = UpstreamConfiguration.from_dict(upstream_config)

            package_sources = []
            package_source_dicts = _optional(config, "package_sources", list, [])
            for package_source_dict in package_source_dicts:
                package_sources.append(PackageSource.from_dict(package_source_dict))

            upload_target_config = _optional(config, "upload_target", dict, None)
            if upload_target_config is not None and "type" not in upload_target_config:
                raise DebutizerYAMLError(
                    "The upload_target object must have a 'type' field"
                )
        except DebutizerYAMLError as ex:
            raise CommandError(f"In {config_file}: {ex}")

        upload_target: Optional[UploadTargetConfiguration]
        if upload_target_config is None:
            upload_target = None
        elif upload_target_config["type"] == S3Configuration.TYPE:
            upload_target = S3Configuration.from_dict(upload_target_config)
        elif upload_target_config["type"] == PPAConfiguration.TYPE:
            upload_target = PPAConfiguration.from_dict(upload_target_config)
        else:
            raise DebutizerYAMLError(
                f"Unknown upload target type '{upload_target_config['type']}'"
            )

        return Configuration(
            distributions=distributions,
            architectures=architectures,
            package_sources=package_sources,
            upstream=upstream,
            upload_target=upload_target,
        )

    def check_validity(self):
        if self.upstream is not None and self.upstream.components is None:
            raise DebutizerYAMLError(
                "If the 'upstream' field is set, that object must have a 'components' "
                "field"
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
    return Path(save_config_path("debutizer")) / "s3" / "credentials.yaml"


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
