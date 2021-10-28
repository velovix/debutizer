from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, TypeVar

from .errors import UnexpectedError
from .relation import PackageRelations

ElemType = TypeVar("ElemType")


class _FieldType(ABC):
    @abstractmethod
    def serialize(self, value: Any) -> str:
        ...

    @abstractmethod
    def deserialize(self, value: str) -> Any:
        ...


class Field:
    class String(_FieldType):
        def serialize(self, value: str) -> str:
            return value

        def deserialize(self, value: str) -> str:
            return value

    class Bool(_FieldType):
        def serialize(self, value: bool) -> str:
            return "yes" if value else "no"

        def deserialize(self, value: str) -> bool:
            return True if value == "yes" else False

    class Array(_FieldType):
        class Separator(Enum):
            COMMAS = 1
            """A single line, with commas between elements"""
            COMMAS_MULTILINE = 2
            """A line per element, with a comma between elements. Usually (always?)
            syntactically the same as COMMAS, but looks better for long lists.
            """
            WHITESPACE_SEPARATED = 3
            """A single line, with spaces between elements"""
            LINE_BASED = 4
            """A line per element, with no other separator"""

        def __init__(self, separator: Separator):
            self._separator = separator

        def serialize(self, value: List[str]) -> str:
            if self._separator is Field.Array.Separator.COMMAS:
                value_str = ", ".join(value)
            elif self._separator is Field.Array.Separator.COMMAS_MULTILINE:
                value_str = ""
                for item in value:
                    value_str += f"\n {item},"
            elif self._separator is Field.Array.Separator.WHITESPACE_SEPARATED:
                value_str = " ".join(value)
            elif self._separator is Field.Array.Separator.LINE_BASED:
                value_str = ""
                for item in value:
                    value_str += f"\n {item}"
            else:
                raise UnexpectedError(f"Unknown separator type: {self._separator}")

            return value_str

        def deserialize(self, value: str) -> List[str]:
            if self._separator in [
                Field.Array.Separator.COMMAS,
                Field.Array.Separator.COMMAS_MULTILINE,
            ]:
                value_list = value.split(",")
            elif self._separator in [
                Field.Array.Separator.WHITESPACE_SEPARATED,
                Field.Array.Separator.LINE_BASED,
            ]:
                value_list = value.split()
            else:
                raise UnexpectedError(f"Unknown separator type: {self._separator}")

            return [v.strip() for v in value_list]

    class PackageRelations(_FieldType):
        def serialize(self, value: PackageRelations) -> str:
            return value.serialize()

        def deserialize(self, value: str) -> PackageRelations:
            return PackageRelations.deserialize(value)

    def __init__(self, name: str, type_: _FieldType = None):
        self.name = name
        self.type = type_ if type_ else Field.String()

    def serialize(self, value: Any) -> str:
        return self.type.serialize(value)

    def deserialize(self, value: str) -> Any:
        value = value.strip()
        return self.type.deserialize(value)
