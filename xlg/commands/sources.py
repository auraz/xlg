"""Source commands that start pipelines."""
from collections.abc import Generator
from pathlib import Path


def cmd_read(path: str) -> Generator[str, None, None]:
    """Read file content."""
    yield Path(path).read_text()
