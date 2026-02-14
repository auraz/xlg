"""Source commands that start pipelines."""
from collections.abc import Generator
from pathlib import Path
import httpx


def cmd_read(path: str) -> Generator[str, None, None]:
    """Read file content."""
    yield Path(path).read_text()


def cmd_fetch(url: str) -> Generator[str, None, None]:
    """Fetch URL content."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    response = httpx.get(url)
    response.raise_for_status()
    yield response.text
