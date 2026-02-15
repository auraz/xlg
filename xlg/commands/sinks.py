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
    """Play music via Apple Music - uses MusicKit API with user token for auto-play."""
    import time
    import httpx
    from xlg.config import get_config

    key_id = get_config('APPLE_MUSIC_KEY_ID')
    team_id = get_config('APPLE_MUSIC_TEAM_ID')
    key_path = get_config('APPLE_MUSIC_KEY_PATH')
    private_key = get_config('APPLE_MUSIC_PRIVATE_KEY')
    user_token = get_config('APPLE_MUSIC_USER_TOKEN')

    if key_path and not private_key:
        with open(os.path.expanduser(key_path)) as f:
            private_key = f.read()

    if key_id and team_id and private_key:
        am = AppleMusic(secret_key=private_key, key_id=key_id, team_id=team_id)
        results = am.search(query, types=['songs'], limit=1)
        songs = results.get('results', {}).get('songs', {}).get('data', [])
        if not songs:
            raise RuntimeError(f"No songs found for: {query}")

        song = songs[0]
        song_id = song['id']
        song_name = song['attributes']['name']

        if user_token:
            import jwt
            dev_token = jwt.encode(
                {"iss": team_id, "iat": int(time.time()), "exp": int(time.time()) + 3600},
                private_key, algorithm="ES256", headers={"alg": "ES256", "kid": key_id}
            )
            headers = {"Authorization": f"Bearer {dev_token}", "Music-User-Token": user_token}
            httpx.post("https://api.music.apple.com/v1/me/library", params={"ids[songs]": song_id}, headers=headers)
            time.sleep(1)
            script = f'tell application "Music" to play (first track of library playlist 1 whose name is "{song_name}")'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
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
