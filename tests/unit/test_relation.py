import pytest
from debian.deb822 import PkgRelation

from debutizer.relation import (
    Dependency,
    PackageRelations,
    Relation,
    SubstitutionRelation,
)


@pytest.mark.parametrize(
    "input_,expected",
    [
        # Basic set of relationships
        (
            "debhelper, debhelper-compat (= 13), dpkg-dev (>= 1.15.1)",
            PackageRelations(
                [
                    Relation([Dependency(name="debhelper")]),
                    Relation(
                        [
                            Dependency(
                                name="debhelper-compat", version="13", relationship="="
                            )
                        ]
                    ),
                    Relation(
                        [
                            Dependency(
                                name="dpkg-dev", version="1.15.1", relationship=">="
                            )
                        ]
                    ),
                ]
            ),
        ),
        # Relationship with multiple options
        (
            "libc6-dev | libc-dev (>= 1:2.4)",
            PackageRelations(
                [
                    Relation(
                        [
                            Dependency(name="libc6-dev"),
                            Dependency(
                                name="libc-dev", version="1:2.4", relationship=">="
                            ),
                        ]
                    )
                ]
            ),
        ),
        # Relationship with architectures specified
        (
            "libunwind-dev [i386 amd64 armel]",
            PackageRelations(
                [
                    Relation(
                        [
                            Dependency(
                                name="libunwind-dev",
                                arch=[
                                    PkgRelation.ArchRestriction(
                                        enabled=True, arch="i386"
                                    ),
                                    PkgRelation.ArchRestriction(
                                        enabled=True, arch="amd64"
                                    ),
                                    PkgRelation.ArchRestriction(
                                        enabled=True, arch="armel"
                                    ),
                                ],
                            )
                        ]
                    )
                ]
            ),
        ),
        # Relationship with restrictions
        (
            "libgmp-dev <!nocheck>",
            PackageRelations(
                [
                    Relation(
                        [
                            Dependency(
                                name="libgmp-dev",
                                restrictions=[
                                    [
                                        PkgRelation.BuildRestriction(
                                            enabled=False, profile="nocheck"
                                        )
                                    ]
                                ],
                            )
                        ]
                    )
                ]
            ),
        ),
        # Relationships with substitutions
        (
            "${shlibs:Depends}, ${misc:Depends}, libcap2-bin [linux-any], "
            "libcool (= ${binary:Version})",
            PackageRelations(
                [
                    SubstitutionRelation("${shlibs:Depends}"),
                    SubstitutionRelation("${misc:Depends}"),
                    Relation(
                        [
                            Dependency(
                                name="libcap2-bin",
                                arch=[
                                    PkgRelation.ArchRestriction(
                                        enabled=True, arch="linux-any"
                                    )
                                ],
                            )
                        ]
                    ),
                    SubstitutionRelation("libcool (= ${binary:Version})"),
                ]
            ),
        ),
    ],
)
def test_parse_package_relations(input_: str, expected: PackageRelations):
    actual = PackageRelations.deserialize(input_)
    assert actual == expected
