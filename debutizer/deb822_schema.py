from typing import Any, Dict, Type, TypeVar

from debian.deb822 import Deb822

from debutizer.deb822_utils import Field

T = TypeVar("T", bound=Deb822)


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

        return deb822

    @classmethod
    def _deserialize_fields(cls, deb822: T) -> Dict[str, Any]:
        inputs = {}

        for attr_name, field in cls.FIELDS.items():
            if field.name in deb822:
                inputs[attr_name] = field.deserialize(deb822[field.name])
            else:
                inputs[attr_name] = None

        return inputs

    @classmethod
    def deserialize(cls, deb822: T):
        inputs = cls._deserialize_fields(deb822)
        return cls(**inputs)
