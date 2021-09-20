import argparse
from pathlib import Path

from ..configuration import Configuration
from ..errors import CommandError
from ..translate import make_translator
from .command import Command, register

tr = make_translator("build_command")


_CONFIG_FILE_NAME = "debutizer.yaml"


@register("build")
class BuildCommand(Command):
    def define_args(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description=tr("description"))

        parser.add_argument(
            "--package-path",
            type=Path,
            default=Path.cwd(),
            required=False,
            help=tr("package-path-help"),
        )

        return parser

    def behavior(self, args: argparse.Namespace) -> None:
        package_dirs = args.package_path.iterdir()
        package_dirs = filter(Path.is_dir, package_dirs)

        for package_dir in package_dirs:
            self._build_package(package_dir)

    def _build_package(self, package_dir: Path):
        config_file = package_dir / _CONFIG_FILE_NAME
        if not config_file.exists():
            error = tr("missing-config-file").format(
                config_file_name=_CONFIG_FILE_NAME,
                package_dir=package_dir.name,
            )
            raise CommandError(error)

        config = Configuration.from_file(config_file)
