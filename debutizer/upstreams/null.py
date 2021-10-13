from pathlib import Path

from .base import Upstream


class NullUpstream(Upstream):
    """An upstream that fetches nothing!"""

    def fetch(self) -> Path:
        self._package_dir().mkdir()
        return self._package_dir()
