import pytest

from debutizer.errors import CommandError
from debutizer.registry import Registry
from debutizer.source_package import SourcePackage


def test_registering_duplicate_packages():
    registry = Registry()

    SourcePackage.distribution = "focal"
    registry.add(MockSourcePackage("mypackage1"))
    with pytest.raises(CommandError):
        registry.add(MockSourcePackage("mypackage1"))


class MockSourcePackage(SourcePackage):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name
