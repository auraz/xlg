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
    """Play music via Apple Music - searches library first, then opens catalog search."""
    script = f'''
    tell application "Music"
        set searchResults to search library playlist 1 for "{query}"
        if (count of searchResults) > 0 then
            play item 1 of searchResults
            return "playing:" & name of item 1 of searchResults
        else
            return "not found"
        end if
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Apple Music error: {result.stderr}")
    output = result.stdout.strip()
    if output.startswith("playing:"):
        return f"Playing: {output[8:]}"
    from urllib.parse import quote
    search_url = f"music://music.apple.com/search?term={quote(query)}"
    subprocess.run(["open", search_url])
    return f"Searching Apple Music for: {query}"


def cmd_open(upstream: Generator[Any, None, None]) -> list[str]:
    """Open URLs in browser."""
    urls = []
    for item in upstream:
        url = item["url"] if isinstance(item, dict) else str(item)
        subprocess.run(["open", url])
        urls.append(url)
    return urls
