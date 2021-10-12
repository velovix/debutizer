import sys
from pathlib import Path
from types import ModuleType
from typing import ClassVar

from .errors import CommandError
from .print_utils import Color, Format, print_color
from .source_package import SourcePackage


class PackagePy:
    FILE_NAME: ClassVar[str] = "package.py"

    source_package: SourcePackage
    component: str
    # pre_build: Callable[[Registry], None]

    def __init__(self, package_file: Path):
        if not package_file.is_file():
            raise CommandError(
                f"Package {package_file.parent.name} is missing a "
                f"{PackagePy.FILE_NAME} file"
            )

        package_module = ModuleType(package_file.name)
        # Put the module in a package so it can do relative imports
        package_module.__package__ = package_file.name

        code = package_file.read_text()
        compiled = compile(code, package_file, "exec")

        try:
            exec(compiled, package_module.__dict__)
        except CommandError:
            # CommandErrors are expected errors that are ready for users to see, so
            # pass them through unchanged
            raise
        except Exception:
            print_color(
                "Unexpected exception while running package.py:",
                color=Color.RED,
                format_=Format.BOLD,
                file=sys.stderr,
            )
            raise

        try:
            self.source_package = package_module.source_package  # type: ignore
        except AttributeError:
            raise CommandError(
                "The package.py file must define a global variable named "
                "'source_package'"
            )
        if not isinstance(self.source_package, SourcePackage):
            raise CommandError(
                f"The source_package variable must be of type {SourcePackage.__name__}"
            )

        # TODO: Type annotate this attribute when this PR makes it into a MyPy release
        #       https://github.com/python/mypy/pull/10548
        self.pre_build = getattr(package_module, "pre_build", lambda _: None)
        if not callable(self.pre_build):
            raise CommandError("The pre_build variable must be a callable")

        self.component = getattr(package_module, "component", "main")
        if not isinstance(self.component, str):
            raise CommandError("The component variable must be a string")
