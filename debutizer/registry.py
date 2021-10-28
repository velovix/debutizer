from typing import Dict

from .errors import CommandError
from .relation import Dependency, Relation
from .source_package import SourcePackage


class NoSuchPackageError(CommandError):
    def __init__(self, package_name: str):
        super().__init__(f"No package with name '{package_name}' exists")
        self.package_name = package_name


class Registry:
    def __init__(self):
        self._packages: Dict[str, SourcePackage] = {}

    def add(self, package: SourcePackage) -> None:
        if package.name in self._packages:
            raise CommandError(
                f"A source package with the name {package.name} has already "
                f"been registered! No two source packages may share the same name."
            )

        self._packages[package.name] = package

    def make_relation(self, package_name: str) -> Relation:
        source_package = None
        binary_package = None

        for source in self._packages.values():
            for binary in source.control.binaries:
                if binary.package == package_name:
                    source_package = source
                    binary_package = binary

        if binary_package is None or source_package is None:
            raise CommandError(
                f"Binary package {package_name} has not been added to the registry"
            )

        dependency = Dependency(
            name=binary_package.package,
            version=source_package.version,
            relationship="=",
        )
        return Relation([dependency])
