from typing import List, Optional

from debian.deb822 import PkgRelation

from debutizer.errors import CommandError


class Dependency:
    def __init__(
        self,
        name: str,
        archqual: Optional[str] = None,
        version: Optional[str] = None,
        relationship: Optional[str] = None,
        arch: Optional[List[PkgRelation.ArchRestriction]] = None,
        restrictions: Optional[List[List[PkgRelation.BuildRestriction]]] = None,
    ):
        self.name = name
        self.archqual = archqual
        self.version = version
        self.relationship = relationship
        self.arch = arch
        self.restrictions = restrictions

    def __repr__(self) -> str:
        value = f"Dependency({self.name}"
        if self.version is not None and self.relationship is not None:
            value += f", version=({self.relationship} {self.version})"

        value += ")"
        return value

    @classmethod
    def deserialize(cls, relation: "PkgRelation.ParsedRelation") -> "Dependency":
        version = None
        relationship = None
        version_tuple = relation.get("version")
        if version_tuple is not None:
            relationship, version = version_tuple

        return Dependency(
            name=relation["name"],
            archqual=relation.get("archqual"),
            version=version,
            relationship=relationship,
            arch=relation.get("arch"),
            restrictions=relation.get("restrictions"),
        )

    def serialize(self) -> "PkgRelation.ParsedRelation":
        version_tuple = None
        if self.version is not None and self.relationship is not None:
            version_tuple = (self.relationship, self.version)

        return {
            "name": self.name,
            "archqual": self.archqual,
            "version": version_tuple,
            "arch": self.arch,
            "restrictions": self.restrictions,
        }


class Relation:
    def __init__(self, dependencies: List[Dependency]):
        self._dependencies = dependencies
        self._iter_index = 0

    def __len__(self) -> int:
        return len(self._dependencies)

    def __setitem__(self, key: int, value: Dependency) -> None:
        self._dependencies[key] = value

    def __getitem__(self, key: int) -> Dependency:
        return self._dependencies[key]

    def __contains__(self, key: int) -> bool:
        return key in self._dependencies

    def __iter__(self) -> "Relation":
        self._iter_index = 0
        return self

    def __next__(self) -> Dependency:
        if self._iter_index >= len(self._dependencies):
            raise StopIteration

        output = self._dependencies[self._iter_index]
        self._iter_index += 1
        return output

    def __repr__(self) -> str:
        dependency_list = ", ".join(str(d) for d in self._dependencies)

        return f"Relation({dependency_list})"

    def intersects(self, other: "Relation") -> bool:
        dependency_names = set(d.name for d in self._dependencies)
        other_dependency_names = set(d.name for d in other._dependencies)

        intersection = dependency_names & other_dependency_names
        return len(intersection) > 0

    @classmethod
    def deserialize(cls, value: List["PkgRelation.ParsedRelation"]) -> "Relation":
        """Deserializes Debian's PkgRelation format.

        :param value: An element of PkgRelation.parse_relations
        :return: Deserialized relation
        """
        dependencies = []

        for relation in value:
            dependencies.append(Dependency.deserialize(relation))

        return Relation(dependencies=dependencies)

    def serialize(self) -> List["PkgRelation.ParsedRelation"]:
        dependencies = []

        for dependency in self._dependencies:
            dependencies.append(dependency.serialize())

        return dependencies

    @classmethod
    def from_string(cls, value: str) -> "Relation":
        pkg_relations = PkgRelation.parse_relations(value)
        if len(pkg_relations) > 1:
            raise CommandError(f"Dependency '{value}' represents multiple dependencies")
        elif len(pkg_relations) == 0:
            raise CommandError(f"Dependency '{value}' is in an invalid format")
        return cls.deserialize(pkg_relations[0])


class PackageRelations:
    def __init__(self, relations: List[Relation]):
        self._relations = relations
        self._iter_index = 0

    def __len__(self) -> int:
        return len(self._relations)

    def __setitem__(self, key: int, value: Relation) -> None:
        self._relations[key] = value

    def __getitem__(self, key: int) -> Relation:
        return self._relations[key]

    def __contains__(self, key: int) -> bool:
        return key in self._relations

    def __iter__(self) -> "PackageRelations":
        self._iter_index = 0
        return self

    def __next__(self) -> Relation:
        if self._iter_index >= len(self._relations):
            raise StopIteration
        value = self._relations[self._iter_index]
        self._iter_index += 1
        return value

    def add_relation(self, new: Relation, replace: bool = False) -> None:
        conflicting = [r for r in self._relations if r.intersects(new)]
        if len(conflicting) > 0:
            if replace:
                for conflict in conflicting:
                    self._relations.remove(conflict)
            else:
                raise CommandError(
                    f"New relation {new} conflicts with existing dependencies: "
                    f"{conflicting}"
                )

        self._relations.append(new)

    @classmethod
    def deserialize(cls, value: str) -> "PackageRelations":
        pkg_relations = PkgRelation.parse_relations(value)
        relations = [Relation.deserialize(r) for r in pkg_relations]
        return PackageRelations(relations)

    def serialize(self) -> str:
        return PkgRelation.str([v.serialize() for v in self._relations])

    @classmethod
    def from_strings(cls, strings: List[str]) -> "PackageRelations":
        return PackageRelations([Relation.from_string(s) for s in strings])
