from typing import Any, Dict, Mapping, Type, TypeVar, Union, cast, no_type_check

from debian.deb822 import Deb822, RestrictedWrapper

from debutizer.deb822_utils import Field

T = TypeVar("T", bound=Deb822)
CLS = TypeVar("CLS", bound="Deb822Schema")

SOURCE = Union[Deb822, RestrictedWrapper]


class Deb822Schema:
    FIELDS: Dict[str, Field]

    def __init__(self, deb822_type: Type[T]):
        self._deb822_type = deb822_type

    def serialize(self) -> T:
        deb822 = self._deb822_type()

        for attr_name, field in self.__class__.FIELDS.items():
            value = self.__getattribute__(attr_name)
            if value is not None:
                deb822[field.name] = field.serialize(value)

        return cast(T, deb822)

    @classmethod
    @no_type_check  # mypy has issues with iterators
    def _deserialize_fields(cls, source: SOURCE) -> Dict[str, Any]:
        inputs = {}

        for attr_name, field in cls.FIELDS.items():
            if field.name in source:
                inputs[attr_name] = field.deserialize(source[field.name])
            else:
                inputs[attr_name] = None

        return inputs

    @classmethod
    def deserialize(cls: Type[CLS], source: SOURCE) -> CLS:
        inputs = cls._deserialize_fields(source)
        return cls(**inputs)
