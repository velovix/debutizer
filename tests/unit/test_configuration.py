import pytest

from debutizer.commands.config_file import (
    CredentialsYAMLError,
    DebutizerYAMLError,
    S3UploadTargetConfiguration,
)


def test_s3_configuration_validity():
    config = S3UploadTargetConfiguration(
        endpoint="my_endpoint",
        bucket="my_bucket",
        access_key="my_access_key",
        secret_key="my_secret_key",
        sign=True,
        gpg_key_id="my_gpg_key_id",
        gpg_signing_key="my_gpg_signing_key",
    )

    config.check_validity()

    config.access_key = None
    with pytest.raises(CredentialsYAMLError):
        config.check_validity()
    config.access_key = "my_access_key"

    config.gpg_key_id = None
    config.gpg_signing_key = None
    with pytest.raises(DebutizerYAMLError):
        config.check_validity()
