from abc import ABC, abstractmethod
from pathlib import Path


class UploadTarget(ABC):
    """A place where packages can be uploaded"""

    @abstractmethod
    def upload(self, artifacts_dir: Path) -> None:
        pass
