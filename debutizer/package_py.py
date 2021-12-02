from pathlib import Path
from types import ModuleType
from typing import ClassVar

from .environment import Environment
from .errors import CommandError
from .print_utils import print_error
from .source_package import SourcePackage


class PackagePy:
    FILE_NAME: ClassVar[str] = "package.py"

    source_package: SourcePackage
    """The source package defined by this configuration"""
    component: str
    """The component of the repository where the configuration's packages will be stored
    """
    # pre_build: Callable[[Registry], None]
    """A callback that will be run before a package is built"""
    build_dir: Path
    """The directory where scratch work will be done for this configuration"""

    def __init__(self, env: Environment, package_py: Path):
        if not package_py.is_file():
            raise CommandError(
                f"Package {package_py.parent.name} is missing a "
                f"{PackagePy.FILE_NAME} file"
            )
        self.build_dir = env.build_root / package_py.parent.name

        package_module = ModuleType(package_py.name)
        # Put the module in a package so it can do relative imports
        package_module.__package__ = package_py.name

        code = package_py.read_text()
        compiled = compile(code, package_py, "exec")

        try:
            exec(compiled, package_module.__dict__)
        except CommandError:
            # CommandErrors are expected errors that are ready for users to see, so
            # pass them through unchanged
            raise
        except Exception:
            print_error("Unexpected exception while running package.py:")
            raise

        try:
            self.source_package = package_module.create_source_package(env)  # type: ignore
        except AttributeError:
            raise CommandError(
                "The package.py file must define a global variable named "
                "'source_package'"
            )
        if not isinstance(self.source_package, SourcePackage):
            raise CommandError(
                f"The source_package variable must be of type {SourcePackage.__name__}"
            )

        # Commit changes to disk
        self.source_package.complete()

        # TODO: Type annotate this attribute when this PR makes it into a MyPy release
        #       https://github.com/python/mypy/pull/10548
        self.pre_build = getattr(
            package_module, "pre_build", lambda *args, **kwargs: None
        )
        if not callable(self.pre_build):
            raise CommandError("The pre_build variable must be a callable")

        self.component = getattr(package_module, "component", "main")
        if not isinstance(self.component, str):
            raise CommandError("The component variable must be a string")

    def __repr__(self) -> str:
        return f"PackagePy(source_package={self.source_package})"
