"""Transform commands for pipelines."""
import csv
import json
import subprocess
from collections.abc import Generator
from io import StringIO
from typing import Any


def cmd_parse(upstream: Generator[Any, None, None], format: str) -> Generator[Any, None, None]:
    """Parse input data according to format."""
    for item in upstream:
        if format == "json":
            parsed = json.loads(item)
            if isinstance(parsed, list):
                yield from parsed
            else:
                yield parsed
        elif format == "csv":
            reader = csv.DictReader(StringIO(item))
            yield from reader


def cmd_get(upstream: Generator[Any, None, None], path: str) -> Generator[Any, None, None]:
    """Extract nested field by dot-path, flattening lists."""
    for item in upstream:
        value = item
        for key in path.split('.'):
            value = value[key]
        if isinstance(value, list):
            yield from value
        else:
            yield value


def cmd_filter(upstream: Generator[Any, None, None], field: str, value: str) -> Generator[Any, None, None]:
    """Filter items where field equals value."""
    for item in upstream:
        if str(item.get(field)) == str(value):
            yield item


def cmd_take(upstream: Generator[Any, None, None], n: int) -> Generator[Any, None, None]:
    """Take first n items."""
    count = 0
    for item in upstream:
        if count >= n:
            break
        yield item
        count += 1


def cmd_sort(upstream: Generator[Any, None, None], field: str) -> Generator[Any, None, None]:
    """Sort items by field."""
    items = list(upstream)
    items.sort(key=lambda x: x.get(field, ""))
    yield from items


def cmd_summarize(upstream: Generator[Any, None, None]) -> Generator[str, None, None]:
    """Summarize text using Apple Intelligence via macOS Shortcuts."""
    for item in upstream:
        text = str(item) if not isinstance(item, str) else item
        result = subprocess.run(["shortcuts", "run", "XLG Summarize", "-i", "-"], input=text, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Shortcut failed: {result.stderr}")
        yield result.stdout.strip()
