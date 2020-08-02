from pathlib import Path


class DirectoryMixin:
    def make_directory(self, path: str) -> Path:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)

        return dir_path
