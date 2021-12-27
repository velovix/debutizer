import re
from typing import Any, List, Optional, Union, cast

from debian.deb822 import PkgRelation

from debutizer._list_backed_container import ListBackedContainer
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
        output = f"Dependency("

        fields = []
        for key, value in self.__dict__.items():
            fields.append(f"{key}={value}")
        output += ", ".join(fields)

        output += ")"
        return output

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Dependency) and self.__dict__ == other.__dict__

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


class Relation(ListBackedContainer[Dependency]):
    def __init__(self, dependencies: List[Dependency]):
        super().__init__()
        self._data = dependencies
        self._iter_index = 0

    def intersects(self, other: "Relation") -> bool:
        dependency_names = set(d.name for d in self._data)
        other_dependency_names = set(d.name for d in other._data)

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

        for dependency in self._data:
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


class SubstitutionRelation:
    """A relation that contains a substitution variable, like '${shlibs:Depends}'.
    Substitution variables are filled in at build-time, so these relations can not be
    parsed statically beforehand.
    """

    def __init__(self, raw_value: str) -> None:
        self.raw_value = raw_value

    def __repr__(self) -> str:
        return f"SubstitutionRelation({self.raw_value})"

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, SubstitutionRelation) and self.__dict__ == other.__dict__
        )

    def serialize(self) -> List["PkgRelation.ParsedRelation"]:
        # Relations with substitutions are represented internally as
        # PkgRelation.ParsedRelation objects with the raw string as the name
        dependency = Dependency(name=self.raw_value)
        return [dependency.serialize()]


RELATION_ITEM = Union[Relation, SubstitutionRelation]


class PackageRelations(ListBackedContainer[RELATION_ITEM]):
    def __init__(self, relations: List[RELATION_ITEM]):
        super().__init__()
        self._data = relations

    def parsed(self) -> List[Relation]:
        """
        :return: A list of Relation objects, with SubstitutionRelations excluded
        """
        return [r for r in self._data if isinstance(r, Relation)]

    def add_relation(self, new: RELATION_ITEM, replace: bool = False) -> None:
        if isinstance(new, Relation):
            # Check if the relation conflicts with another. We can't check
            # SubstitutionRelations for conflicts since they can't be statically parsed.
            conflicting = [
                r for r in self._data if isinstance(r, Relation) and r.intersects(new)
            ]
            if len(conflicting) > 0:
                if replace:
                    for conflict in conflicting:
                        self._data.remove(conflict)
                else:
                    raise CommandError(
                        f"New relation {new} conflicts with existing dependencies: "
                        f"{conflicting}"
                    )

        self._data.append(new)

    @classmethod
    def deserialize(cls, value: str) -> "PackageRelations":
        relations: List[RELATION_ITEM] = []

        # We need to do some parsing of our own here to check each relation for
        # substitution variables. If any exist, we avoid trying to parse them as a
        # PkgRelation.ParsedRelation.
        relation: RELATION_ITEM
        relation_strs = cls._SEPARATOR.split(value.strip())
        for relation_str in relation_strs:
            if cls._SUBSTITUTION.search(relation_str):
                relation = SubstitutionRelation(relation_str)
            else:
                pkg_relation = PkgRelation.parse_relations(relation_str)[0]
                relation = Relation.deserialize(pkg_relation)
            relations.append(relation)

        return PackageRelations(relations)

    def serialize(self) -> str:
        relation = PkgRelation.str([v.serialize() for v in self._data])
        return cast(str, relation)

    @classmethod
    def from_strings(cls, strings: List[str]) -> "PackageRelations":
        return PackageRelations.deserialize(",".join(strings))

    _SEPARATOR = re.compile(r"\s*,\s*")
    _SUBSTITUTION = re.compile(r"\${.*?}")
