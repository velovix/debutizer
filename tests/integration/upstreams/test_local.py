import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from debutizer.commands.build import BuildCommand
from debutizer.commands.configuration import Configuration


def test_build_source_package_upstream_package():
    command = BuildCommand()

    with TemporaryDirectory() as artifacts_dir:
        args = argparse.Namespace(
            package_dir=Path("tests/resources/local_upstreams"),
            artifacts_dir=Path(artifacts_dir),
            config_file=Path("whatever"),
        )
        config = Configuration(
            distribution="focal",
            architecture="amd64",
        )
        command.parse_args = Mock(return_value=args)
        command.parse_config_file = Mock(return_value=config)
        command.run()
