"""Transform commands for pipelines."""
import csv
import json
from collections.abc import Generator
from io import StringIO
from typing import Any


def cmd_parse(upstream: Generator[Any, None, None], format: str) -> Generator[Any, None, None]:
    """Parse input data according to format."""
    for item in upstream:
        if format == "json":
            yield json.loads(item)
        elif format == "csv":
            reader = csv.DictReader(StringIO(item))
            yield from reader
