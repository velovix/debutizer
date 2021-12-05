from .abstract import UploadTarget
from .ppa import PPAUploadTarget
from .s3 import S3UploadTarget

__all__ = [
    "UploadTarget",
    "PPAUploadTarget",
    "S3UploadTarget",
]
