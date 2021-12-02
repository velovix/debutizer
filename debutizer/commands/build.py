import argparse
import shutil

import requests

from ..environment import Environment
from ..errors import CommandError
from ..package_py import PackagePy
from ..print_utils import print_color, print_done, print_header, print_notify
from ..registry import Registry
from .command import Command
from .config_file import Configuration, PackageSource, UpstreamConfiguration
from .env_argparse import EnvArgumentParser
from .local_repo import LocalRepository
from .repo_metadata import add_packages_files, add_release_files, add_sources_files
from .utils import (
    build_package,
    copy_binary_artifacts,
    copy_source_artifacts,
    find_package_dirs,
    make_build_dir,
    make_chroot,
    make_source_files,
    process_package_pys,
    set_chroot_package_sources,
)


class BuildCommand(Command):
    def __init__(self):
        super().__init__()
        self.parser = EnvArgumentParser(
            prog="debutizer build", description="Makes source and binary packages"
        )

        self.add_artifacts_dir_flag()
        self.add_config_file_flag()
        self.add_package_dir_flag()

        self.parser.add_argument(
            "--shell-on-failure",
            action="store_true",
            help="If provided, a shell will be started in the build chroot if the "
            "build fails",
        )

    def behavior(self, args: argparse.Namespace) -> None:
        config = self.parse_config_file(args)

        if args.artifacts_dir.is_dir():
            shutil.rmtree(args.artifacts_dir)
        args.artifacts_dir.mkdir()

        registry = Registry()
        local_repo = LocalRepository(port=8080, artifacts_dir=args.artifacts_dir)
        local_repo.start()
        self.cleanup_hooks.append(local_repo.close)

        for arch in config.architectures:
            for distro in config.distributions:
                build_dir = make_build_dir()

                env = Environment(
                    codename=distro,
                    architecture=arch,
                    package_root=args.package_dir,
                    build_root=build_dir,
                    artifacts_root=args.artifacts_dir,
                )

                _build_packages(
                    env=env,
                    config=config,
                    registry=registry,
                    shell_on_failure=args.shell_on_failure,
                )

        print_color("")
        print_done("Build complete!")


def _build_packages(
    env: Environment, config: Configuration, registry: Registry, shell_on_failure: bool
) -> None:
    """Builds packages for the given distribution/architecture pair"""

    print_header(
        f"Building packages for distribution '{env.codename}' on architecture "
        f"'{env.architecture}'"
    )

    package_dirs = find_package_dirs(env.package_root)
    chroot_archive_path = make_chroot(env.codename)
    package_pys = process_package_pys(env, package_dirs, registry)

    if config.upstream is not None:
        new_package_pys = []
        for package_py in package_pys:
            if _exists_upstream(config.upstream.url, env.codename, package_py):
                print_color(
                    f"Package {package_py.source_package.name} already exists "
                    f"upstream, so it will not be built"
                )
            else:
                new_package_pys.append(package_py)
        package_pys = new_package_pys

    print_color("")
    if len(package_pys) > 0:
        print_notify("Building the following packages in this order:")
        for package_py in package_pys:
            print_color(f" * {package_py.source_package.name}")
    else:
        print_notify("No packages will be built")

    for i, package_py in enumerate(package_pys):
        print_color("")
        print_notify(f"Building {package_py.source_package.name}")

        package_sources = []
        if config.upstream is not None:
            entry = _make_upstream_source_entry(config.upstream, env.codename)
            package_sources.append(entry)
        if i > 0:
            # We can't add the local repo if this is the first package being built
            # because APT does not like empty repositories
            package_source = PackageSource(
                entry=f"deb [trusted=yes] http://localhost:8080 {env.codename} main"
            )
            package_sources.append(package_source)
        package_sources += config.package_sources
        set_chroot_package_sources(env.codename, package_sources)

        source_results_dir = make_source_files(
            env.build_root, package_py.source_package
        )
        binary_results_dir = build_package(
            source_package=package_py.source_package,
            build_dir=env.build_root,
            chroot_archive_path=chroot_archive_path,
            network_access=env.network_access,
            shell_on_failure=shell_on_failure,
        )

        copy_source_artifacts(
            results_dir=source_results_dir,
            artifacts_dir=env.artifacts_root,
            distribution=env.codename,
            component=package_py.component,
        )
        copy_binary_artifacts(
            results_dir=binary_results_dir,
            artifacts_dir=env.artifacts_root,
            distribution=env.codename,
            component=package_py.component,
            architecture=env.architecture,
        )

        print_notify("Updating metadata files...")
        add_packages_files(env.artifacts_root)
        add_sources_files(env.artifacts_root)
        add_release_files(
            env.artifacts_root,
            sign=False,
            gpg_key_id=None,
            gpg_signing_key=None,
            gpg_signing_password=None,
        )


def _make_upstream_source_entry(
    upstream: UpstreamConfiguration, distribution: str
) -> PackageSource:
    """Creates an APT source list entry based on the provided configuration"""
    parameters = ""
    if upstream.is_trusted:
        parameters = "[trusted=yes]"

    components_str = " ".join(upstream.components)

    return PackageSource(
        entry=f"deb {parameters} {upstream.url} {distribution} {components_str}",
        gpg_key_url=upstream.gpg_key_url,
    )


def _exists_upstream(
    upstream_url: str, distribution: str, package_py: PackagePy
) -> bool:
    """Check if the package already exists upstream at the current version by seeing if
    the Debian upstream source file is already uploaded.
    """
    if upstream_url[:-1] == "/":
        upstream_url = upstream_url[:-1]

    url = (
        f"{upstream_url}"
        f"/dists"
        f"/{distribution}"
        f"/{package_py.component}"
        f"/source"
        f"/{package_py.source_package.name}_{package_py.source_package.version}.dsc"
    )

    try:
        response = requests.head(url)
    except requests.RequestException as ex:
        raise CommandError(f"While contacting the upstream repo: {ex}") from ex
    if response.ok:
        return True
    elif response.status_code in [requests.codes.forbidden, requests.codes.not_found]:
        # Most S3-compatible buckets return forbidden codes when files do not exist
        return False
    else:
        raise CommandError(
            f"Unexpected status code {response.status_code}: {response.text}"
        )
