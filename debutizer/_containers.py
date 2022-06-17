from pathlib import Path
from typing import Any, Callable, Generic, List, TypeVar

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


class NewlineSeparatedFile(ListBackedContainer[T], Generic[T]):
    """Manages a list of objects that are saved and loaded from a file of
    newline-separated items
    """

    def __init__(
        self,
        target_file: Path,
        create_func: Callable[[str], T],
        to_str_func: Callable[[T], str] = str,
    ) -> None:
        super().__init__()
        self._target_file = target_file
        self._create_func = create_func
        self._to_str_func = to_str_func

    def add(self, item: T) -> None:
        self._data.append(item)

    def save(self) -> None:
        if len(self) > 0:
            file_ = self._target_file
            content = "\n".join(self._to_str_func(p) for p in self)
            file_.write_text(content)

    def load(self) -> None:
        file_ = self._target_file
        if file_.is_file():
            strs = file_.read_text().split("\n")
            # Filter out empty lines
            strs = [s for s in strs if len(s.strip()) > 0]
            self._data = [self._create_func(s) for s in strs]
