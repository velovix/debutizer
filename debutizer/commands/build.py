import argparse
import shutil
from typing import List

import requests

from ..environment import Environment
from ..errors import CommandError
from ..package_py import PackagePy
from ..print_utils import Color, Format, print_color, print_done
from ..registry import Registry
from ..source_package import SourcePackage
from ..upstreams import Upstream
from .command import Command
from .config import EnvArgumentParser
from .local_repo import LocalRepository
from .repo_metadata import add_packages_files, add_release_files, add_sources_files
from .utils import (
    build_package,
    copy_binary_artifacts,
    copy_source_artifacts,
    find_package_dirs,
    make_chroot,
    make_source_files,
    process_package_pys,
    set_chroot_repos,
)


class BuildCommand(Command):
    def __init__(self):
        self.parser = EnvArgumentParser(
            prog="debutizer build", description="Builds your APT packages"
        )

        self.add_common_args()

        self.parser.add_env_flag(
            "--upstream-repo",
            type=str,
            required=False,
            help="An upstream repository to check against before building packages. If "
            "a package at the current version already exists upstream, it will not be "
            "built again. Packages can also pull dependencies down from this "
            "repository where necessary.",
        )
        self.parser.add_env_flag(
            "--upstream-is-trusted",
            action="store_true",
            help="If provided, the upstream repository will be set as a trusted "
            "repository in the build chroot. This allows the repository contents to be "
            "unsigned.",
        )
        self.parser.add_env_flag(
            "--upstream-components",
            nargs="+",
            default=["main"],
            help="The components to include in the build chroot from the upstream "
            "repository. By default, the main component is included.",
        )

    def behavior(self, args: argparse.Namespace) -> None:
        args.artifacts_dir.mkdir(exist_ok=True)
        registry = Registry()
        local_repo = LocalRepository(port=8080, artifacts_dir=args.artifacts_dir)
        local_repo.start()
        self.cleanup_hooks.append(local_repo.close)

        Environment.codename = args.distribution
        Environment.architecture = args.architecture

        if args.build_dir.is_dir():
            shutil.rmtree(args.build_dir)
        args.build_dir.mkdir()

        Upstream.package_root = args.package_dir
        Upstream.build_root = args.build_dir
        SourcePackage.distribution = args.distribution

        package_dirs = find_package_dirs(args.package_dir)
        chroot_archive_path = make_chroot(args.distribution)
        package_pys = process_package_pys(package_dirs, registry, args.build_dir)

        if args.upstream_repo is not None:
            new_package_pys = []
            for package_py in package_pys:
                if _exists_upstream(args.upstream_repo, args.distribution, package_py):
                    print(
                        f"Package {package_py.source_package.name} already exists "
                        f"upstream, so it will not be built"
                    )
                else:
                    new_package_pys.append(package_py)
            package_pys = new_package_pys

        print("")
        if len(package_pys) > 0:
            print_color(
                "Building the following packages in this order:",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )
            for package_py in package_pys:
                print(f" * {package_py.source_package.name}")
        else:
            print_color(
                "No packages will be built",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

        for i, package_py in enumerate(package_pys):
            print("")
            print_color(
                f"Building {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

            repositories = []
            if args.upstream_repo is not None:
                entry = _make_upstream_source_entry(
                    upstream_repo=args.upstream_repo,
                    distribution=args.distribution,
                    components=args.upstream_components,
                    trusted=args.upstream_is_trusted,
                )
                repositories.append(entry)
            if i > 0:
                # We can't add the local repo if this is the first package being built
                # because APT does not like empty repositories
                repositories.append(
                    f"deb [trusted=yes] http://localhost:8080 {args.distribution} main"
                )
            set_chroot_repos(args.distribution, repositories)

            source_results_dir = make_source_files(
                args.build_dir, package_py.source_package
            )
            binary_results_dir = build_package(
                package_py.source_package,
                args.build_dir,
                chroot_archive_path,
            )

            copy_source_artifacts(
                results_dir=source_results_dir,
                artifacts_dir=args.artifacts_dir,
                distribution=args.distribution,
                component=package_py.component,
            )
            copy_binary_artifacts(
                results_dir=binary_results_dir,
                artifacts_dir=args.artifacts_dir,
                distribution=args.distribution,
                component=package_py.component,
                architecture=args.architecture,
            )

            add_packages_files(args.artifacts_dir)
            add_sources_files(args.artifacts_dir)
            add_release_files(args.artifacts_dir, sign=False, gpg_key_id=None)

        print("")
        print_done("Build")


def _make_upstream_source_entry(
    upstream_repo: str,
    distribution: str,
    components: List[str],
    trusted: bool,
) -> str:
    """Creates an APT source list entry based on the provided configuration"""
    parameters = ""
    if trusted:
        parameters = "[trusted=yes]"

    components_str = " ".join(components)

    return f"deb {parameters} {upstream_repo} {distribution} {components_str}"


def _exists_upstream(
    upstream_repo: str, distribution: str, package_py: PackagePy
) -> bool:
    """Check if the package already exists upstream at the current version by seeing if
    the Debian upstream source file is already uploaded.
    """
    if upstream_repo[:-1] == "/":
        upstream_repo = upstream_repo[:-1]

    url = (
        f"{upstream_repo}"
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
