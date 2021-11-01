import gzip
from pathlib import Path
from typing import List


def save_metadata_files(path: Path, contents: str) -> List[Path]:
    """Saves the metadata file and the corresponding compressed version of the
    file.

    :param path: The path to save the uncompressed metadata file at
    :param contents: The data to save
    :return: The newly created files
    """
    new_files = []

    contents_bytes = contents.encode()
    path.write_bytes(contents_bytes)
    new_files.append(path)

    compressed_file = path.with_suffix(".gz")
    with gzip.open(compressed_file, "wb") as f:
        f.write(contents_bytes)
    new_files.append(compressed_file)

    return new_files
