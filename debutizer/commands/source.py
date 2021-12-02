import argparse
import shutil

from ..environment import Environment
from ..print_utils import print_color, print_done, print_header, print_notify
from ..registry import Registry
from .command import Command
from .env_argparse import EnvArgumentParser
from .utils import (
    copy_source_artifacts,
    find_package_dirs,
    make_build_dir,
    make_source_files,
    process_package_pys,
)


class SourceCommand(Command):
    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer source", description="Makes source packages"
        )

        self.add_artifacts_dir_flag()
        self.add_config_file_flag()
        self.add_package_dir_flag()

    def behavior(self, args: argparse.Namespace) -> None:
        config = self.parse_config_file(args)
        registry = Registry()

        if args.artifacts_dir.is_dir():
            shutil.rmtree(args.artifacts_dir)
        args.artifacts_dir.mkdir()

        for distro in config.distributions:
            build_dir = make_build_dir()

            env = Environment(
                codename=distro,
                architecture="",
                package_root=args.package_dir,
                build_root=build_dir,
                artifacts_root=args.artifacts_dir,
            )

            _source_packages(registry, env)

        print_color("")
        print_done("Source complete!")


def _source_packages(registry: Registry, env: Environment) -> None:
    print_header(f"Sourcing packages for distribution {env.codename}")

    package_dirs = find_package_dirs(env.package_root)
    package_pys = process_package_pys(env, package_dirs, registry)

    for package_py in package_pys:
        print_notify(f"Sourcing {package_py.source_package.name}")

        results_dir = make_source_files(env.build_root, package_py.source_package)

        copy_source_artifacts(
            results_dir=results_dir,
            artifacts_dir=env.artifacts_root,
            distribution=env.codename,
            component=package_py.component,
        )
