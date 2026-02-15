"""Sink commands that consume pipelines."""

import sqlite3
import subprocess
from collections.abc import Generator
from typing import Any


def cmd_print(upstream: Generator[Any, None, None]) -> list[Any]:
    """Print each item and return collected results."""
    results = []
    for item in upstream:
        print(item)
        results.append(item)
    return results


def cmd_write(upstream: Generator[Any, None, None], path: str) -> int:
    """Write items to file."""
    count = 0
    with open(path, "w") as f:
        for item in upstream:
            f.write(str(item))
            count += 1
    return count


def cmd_store(upstream: Generator[Any, None, None], path: str) -> int:
    """Store items in SQLite database."""
    conn = sqlite3.connect(path)
    count = 0
    for item in upstream:
        if isinstance(item, dict):
            if count == 0:
                cols = ", ".join(item.keys())
                placeholders = ", ".join("?" * len(item))
                conn.execute(f"CREATE TABLE IF NOT EXISTS data ({cols})")
            conn.execute(f"INSERT INTO data VALUES ({placeholders})", list(item.values()))
            count += 1
    conn.commit()
    conn.close()
    return count


def cmd_play(query: str) -> str:
    """Play music via Shortcuts - searches Apple Music catalog."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(query)
        input_path = f.name
    result = subprocess.run(["shortcuts", "run", "Play Music", "-i", input_path], capture_output=True, text=True)
    import os
    os.unlink(input_path)
    if result.returncode != 0:
        raise RuntimeError(f"Shortcut error: {result.stderr.strip() or 'Shortcut \"Play Music\" not found'}")
    return f"Playing: {query}"


def cmd_open(upstream: Generator[Any, None, None]) -> list[str]:
    """Open URLs in browser."""
    urls = []
    for item in upstream:
        url = item["url"] if isinstance(item, dict) else str(item)
        subprocess.run(["open", url])
        urls.append(url)
    return urls
