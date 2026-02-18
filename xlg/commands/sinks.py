"""Sink commands that consume pipelines."""

import sqlite3
import subprocess
from collections.abc import Generator
from typing import Any

from xlg_player import player


def cmd_pause() -> str:
    """Pause playback."""
    return player.pause()


def cmd_resume() -> str:
    """Resume playback."""
    return player.resume()


def cmd_toggle() -> str:
    """Toggle play/pause."""
    return player.toggle()


def cmd_skip() -> str:
    """Skip to next track."""
    return player.skip()


def cmd_previous() -> str:
    """Go to previous track."""
    return player.previous()


def cmd_volume(level: str) -> str:
    """Set or adjust volume (0-100, +10, -10)."""
    return player.volume(level)


def cmd_status() -> str:
    """Get player status as JSON."""
    return player.status()


def cmd_favorite() -> str:
    """Toggle favorite on current track."""
    return player.favorite()


def cmd_play(query: str) -> str:
    """Play music via xlg-player."""
    return player.play(query)


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


def cmd_open(upstream: Generator[Any, None, None]) -> list[str]:
    """Open URLs in browser."""
    urls = []
    for item in upstream:
        url = item["url"] if isinstance(item, dict) else str(item)
        subprocess.run(["open", url])
        urls.append(url)
    return urls
