import argparse
import shutil

import requests

from ..environment import Environment
from ..errors import CommandError
from ..package_py import PackagePy
from ..print_utils import Color, Format, print_color, print_done
from ..registry import Registry
from ..source_package import SourcePackage
from ..upstreams import Upstream
from .command import Command
from .utils import (
    build_package,
    copy_binary_artifacts,
    copy_source_artifacts,
    get_package_dirs,
    make_chroot,
    make_source_files,
    process_package_pys,
)


class BuildCommand(Command):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="debutizer build", description="Builds your APT packages"
        )

        self.add_common_args()

        self.parser.add_argument(
            "--upstream-repo",
            type=str,
            required=False,
            help="An upstream repository to check against before building packages. If "
            "a package at the current version already exists upstream, it will not be "
            "built again. Packages can also pull dependencies down from this "
            "repository where necessary.",
        )

    def behavior(self, args: argparse.Namespace) -> None:
        registry = Registry()

        Environment.codename = args.distribution
        Environment.architecture = args.architecture

        if args.build_dir.is_dir():
            shutil.rmtree(args.build_dir)
        args.build_dir.mkdir()

        Upstream.package_root = args.package_dir
        Upstream.build_root = args.build_dir
        SourcePackage.distribution = args.distribution

        package_dirs = get_package_dirs(args.package_dir)
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

        for package_py in package_pys:
            print("")
            print_color(
                f"Building {package_py.source_package.name}",
                color=Color.MAGENTA,
                format_=Format.BOLD,
            )

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

        print("")
        print_done("Build")


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
