"""Sink commands that consume pipelines."""

import os
import sqlite3
import subprocess
from collections.abc import Generator
from typing import Any

from applemusicpy import AppleMusic


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
    """Play music via Apple Music catalog using native MusicKit player."""
    from pathlib import Path
    from xlg.config import get_config

    key_id = get_config('APPLE_MUSIC_KEY_ID')
    team_id = get_config('APPLE_MUSIC_TEAM_ID')
    key_path = get_config('APPLE_MUSIC_KEY_PATH')
    private_key = get_config('APPLE_MUSIC_PRIVATE_KEY')

    if key_path and not private_key:
        with open(os.path.expanduser(key_path)) as f:
            private_key = f.read()

    if key_id and team_id and private_key:
        am = AppleMusic(secret_key=private_key, key_id=key_id, team_id=team_id)
        player_app = Path.home() / "Applications" / "XlgPlayer.app" / "Contents" / "MacOS" / "xlg-player"
        is_playlist = 'playlist' in query.lower()

        if is_playlist:
            import re
            search_query = re.sub(r'\bplaylist\b', '', query, flags=re.IGNORECASE).strip()
            results = am.search(search_query, types=['playlists'], limit=1)
            playlists = results.get('results', {}).get('playlists', {}).get('data', [])
            if not playlists:
                raise RuntimeError(f"No playlists found for: {query}")
            playlist = playlists[0]
            playlist_id = playlist['id']
            playlist_name = playlist['attributes']['name']
            if player_app.exists():
                subprocess.Popen([str(player_app), '--playlist', playlist_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Playing playlist: {playlist_name}"
            subprocess.run(["open", f"music://music.apple.com/us/playlist/{playlist_id}"])
            return f"Opening playlist: {playlist_name}"

        results = am.search(query, types=['songs'], limit=1)
        songs = results.get('results', {}).get('songs', {}).get('data', [])
        if not songs:
            raise RuntimeError(f"No songs found for: {query}")
        song = songs[0]
        song_id = song['id']
        song_name = song['attributes']['name']
        if player_app.exists():
            subprocess.Popen([str(player_app), song_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Playing: {song_name}"
        subprocess.run(["open", f"music://music.apple.com/us/song/{song_id}"])
        return f"Opening: {song_name} (click to play)"

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
    subprocess.run(["open", f"music://music.apple.com/search?term={quote(query)}"])
    return f"Searching Apple Music for: {query}"


def cmd_open(upstream: Generator[Any, None, None]) -> list[str]:
    """Open URLs in browser."""
    urls = []
    for item in upstream:
        url = item["url"] if isinstance(item, dict) else str(item)
        subprocess.run(["open", url])
        urls.append(url)
    return urls
