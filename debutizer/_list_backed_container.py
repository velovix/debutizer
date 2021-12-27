from typing import Any, Generic, List, TypeVar

T = TypeVar("T")


class ListBackedContainer(Generic[T]):
    def __init__(self) -> None:
        self._data: List[T] = []
        self._iter_index = 0

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ListBackedContainer) and self._data == other._data

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, key: int, value: T) -> None:
        self._data[key] = value

    def __getitem__(self, key: int) -> T:
        return self._data[key]

    def __contains__(self, item: T) -> bool:
        return item in self._data

    def __iter__(self) -> "ListBackedContainer[T]":
        self._iter_index = 0
        return self

    def __next__(self) -> T:
        if self._iter_index >= len(self._data):
            raise StopIteration

        output = self._data[self._iter_index]
        self._iter_index += 1
        return output

    def __repr__(self) -> str:
        output = f"{type(self).__name__}(["
        output += ", ".join(str(d) for d in self._data)
        output += "])"

        return output
