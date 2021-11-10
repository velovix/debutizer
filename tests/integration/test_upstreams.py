import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pytest

from debutizer.commands import BuildCommand
from debutizer.commands.configuration import Configuration


@pytest.mark.parametrize(
    "package_dir",
    [
        Path("tests/resources/local_upstreams"),
        Path("tests/resources/source_package_upstreams"),
        Path("tests/resources/source_repository_upstreams"),
    ],
)
def test_building_packages_from_upstreams(package_dir: Path):
    _build_packages(package_dir)


def _build_packages(package_dir: Path):
    command = BuildCommand()

    with TemporaryDirectory() as artifacts_dir:
        args = argparse.Namespace(
            package_dir=package_dir,
            artifacts_dir=Path(artifacts_dir),
            config_file=Path("unused"),
        )
        config = Configuration(
            distributions=["focal"],
            architectures=["amd64"],
        )
        command.parse_args = Mock(return_value=args)
        command.parse_config_file = Mock(return_value=config)
        command.run()
