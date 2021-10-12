from typing import Dict, Optional

from .errors import CommandError
from .source_package import SourcePackage


class NoSuchPackageError(CommandError):
    def __init__(self, package_name: str):
        super().__init__(f"No package with name '{package_name}' exists")
        self.package_name = package_name


class Registry:
    def __init__(self):
        self._packages: Dict[str, SourcePackage] = {}

    def add(self, source_package: SourcePackage) -> None:
        if source_package.name in self._packages:
            raise CommandError(
                f"A source package with the name {source_package.name} has already "
                f"been registered! No two source packages may share the same name."
            )

        self._packages[source_package.name] = source_package

    def require(self, name: str) -> SourcePackage:
        try:
            return self._packages[name]
        except KeyError:
            raise NoSuchPackageError(name)

    def get(self, name: str) -> Optional[SourcePackage]:
        return self._packages.get(name)
