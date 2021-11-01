import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from debutizer.commands.build import BuildCommand


def test_build_source_repository_upstream_package():
    command = BuildCommand()

    with TemporaryDirectory() as build_dir, TemporaryDirectory() as artifacts_dir:
        args = argparse.Namespace(
            package_dir=Path("tests/resources/source_repository_upstreams"),
            build_dir=Path(build_dir),
            artifacts_dir=Path(artifacts_dir),
            distribution="focal",
            architecture="amd64",
            upstream_repo=None,
        )
        command.parse_args = Mock(return_value=args)
        command.run()
