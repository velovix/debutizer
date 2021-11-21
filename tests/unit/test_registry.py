from pathlib import Path

import pytest

from debutizer.environment import Environment
from debutizer.errors import CommandError
from debutizer.registry import Registry
from debutizer.source_package import SourcePackage


def test_registering_duplicate_packages():
    registry = Registry()
    env = Environment(
        codename="focal",
        architecture="amd64",
        package_root=Path("whatever"),
        build_root=Path("something"),
        artifacts_root=Path("something_else"),
    )

    registry.add(env, MockSourcePackage("mypackage1"))
    with pytest.raises(CommandError):
        registry.add(env, MockSourcePackage("mypackage1"))


class MockSourcePackage(SourcePackage):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name
