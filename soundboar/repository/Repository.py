from os import PathLike
from pathlib import Path
from typing import Iterator, BinaryIO, Iterable


class Repository:
    root: Path = None
    supported_file_types: set[str] = None

    def __init__(self, directory: PathLike, supported_files: Iterable[str]):
        self.root = Path(directory)
        self.supported_file_types = set(supported_files)
        if not self.root.is_dir():
            raise ValueError(f"Path is no valid directory: {directory}")

    def file(self, identifier: str) -> Path:
        """
        Get a file path by its identifier
        :param identifier: Identifier of the file to retrieve
        :return: File path
        """
        return self.root / identifier

    def file_position(self, identifier: str) -> int:
        """
        Get the position/index of the file in the repo.
        :param identifier: Identifier of the file
        :return: File position/index
        """
        i = 0
        for (file, *_) in self.all():
            if file == identifier:
                return i
            i += 1
        raise FileNotFoundError(f"File {identifier} does not exist")

    def file_info(self, identifier: str) -> tuple[str, str, Path]:
        """
        Get the ID, name and path of a file by its identifier
        :param identifier: Identifier of the file to get the info of
        :return: ID, name and path of the tile
        """
        file = self.file(identifier)
        return identifier, file.stem, file

    def all(self) -> Iterator[tuple[str, str, Path]]:
        """
        Get the IDs, names and paths of all files in the repository
        :return: Tuples of ID, name and path
        """
        for file_type in self.supported_file_types:
            for file in self.root.rglob("*" + file_type):
                f = file.relative_to(self.root)
                yield self.file_info(str(f))

    async def write(self, file: BinaryIO, identifier: str):
        # TODO: make async
        with open(self.root / identifier, mode="xb") as f:
            file.seek(0)
            f.write(file.read())
        return self.file_info(identifier)

    def delete(self, identifier: str):
        file = self.file(identifier)
        if file.is_file():
            file.unlink(missing_ok=True)
