# MusicKit Play Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable `play` command to search and auto-play any song from Apple Music catalog using MusicKit API.

**Architecture:** Search Apple Music catalog via `apple-music-python`, extract song ID from first result, open `music://` URL to trigger playback in Music.app. Falls back to current behavior if credentials not configured.

**Tech Stack:** apple-music-python, subprocess, environment variables

---

### Task 1: Add apple-music-python dependency

**Files:**
- Modify: `pyproject.toml:6-10`

**Step 1: Add dependency**

Edit `pyproject.toml` dependencies:

```toml
dependencies = [
    "apple-music-python>=2.0.0",
    "feedparser>=6.0.12",
    "httpx>=0.27",
    "openai>=2.21.0",
]
```

**Step 2: Sync dependencies**

Run: `uv sync`
Expected: Successfully installed apple-music-python

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add apple-music-python dependency"
```

---

### Task 2: Write failing test for MusicKit play

**Files:**
- Create: `xlg/commands/sinks_test.py` (add test)

**Step 1: Write the failing test**

Add to `xlg/commands/sinks_test.py`:

```python
def test_cmd_play_musickit_searches_catalog(mocker):
    """Test play uses MusicKit API when credentials available."""
    mocker.patch.dict('os.environ', {
        'APPLE_MUSIC_KEY_ID': 'test-key-id',
        'APPLE_MUSIC_TEAM_ID': 'test-team-id',
        'APPLE_MUSIC_PRIVATE_KEY': 'test-private-key',
    })
    mock_am = mocker.MagicMock()
    mock_am.search.return_value = {
        'results': {'songs': {'data': [{'id': '123456789'}]}}
    }
    mocker.patch('xlg.commands.sinks.AppleMusic', return_value=mock_am)
    mock_open = mocker.patch('subprocess.run')

    from xlg.commands.sinks import cmd_play
    result = cmd_play("Gorillaz")

    mock_am.search.assert_called_once_with('Gorillaz', types=['songs'], limit=1)
    mock_open.assert_called_once()
    assert 'music://music.apple.com' in mock_open.call_args[0][0][1]
    assert '123456789' in mock_open.call_args[0][0][1]
    assert 'Playing' in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/commands/sinks_test.py::test_cmd_play_musickit_searches_catalog -v`
Expected: FAIL with "AppleMusic" import error or similar

**Step 3: Commit**

```bash
git add xlg/commands/sinks_test.py
git commit -m "test: add failing test for MusicKit play"
```

---

### Task 3: Implement MusicKit play

**Files:**
- Modify: `xlg/commands/sinks.py:45-60`

**Step 1: Implement MusicKit integration**

Replace `cmd_play` function in `xlg/commands/sinks.py`:

```python
def cmd_play(query: str) -> str:
    """Play music via Apple Music - uses MusicKit API if configured, else library search."""
    import os
    key_id = os.environ.get('APPLE_MUSIC_KEY_ID')
    team_id = os.environ.get('APPLE_MUSIC_TEAM_ID')
    private_key = os.environ.get('APPLE_MUSIC_PRIVATE_KEY')
    key_path = os.environ.get('APPLE_MUSIC_KEY_PATH')

    if key_path and not private_key:
        with open(os.path.expanduser(key_path)) as f:
            private_key = f.read()

    if key_id and team_id and private_key:
        from applemusicpy import AppleMusic
        am = AppleMusic(secret_key=private_key, key_id=key_id, team_id=team_id)
        results = am.search(query, types=['songs'], limit=1)
        songs = results.get('results', {}).get('songs', {}).get('data', [])
        if not songs:
            raise RuntimeError(f"No songs found for: {query}")
        song_id = songs[0]['id']
        subprocess.run(["open", f"music://music.apple.com/us/song/{song_id}"])
        return f"Playing: {query}"

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
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest xlg/commands/sinks_test.py::test_cmd_play_musickit_searches_catalog -v`
Expected: PASS

**Step 3: Run all tests**

Run: `uv run pytest -q`
Expected: All tests pass

**Step 4: Commit**

```bash
git add xlg/commands/sinks.py
git commit -m "feat: implement MusicKit API for play command"
```

---

### Task 4: Add test for fallback behavior

**Files:**
- Modify: `xlg/commands/sinks_test.py`

**Step 1: Write test for fallback when no credentials**

Add to `xlg/commands/sinks_test.py`:

```python
def test_cmd_play_falls_back_to_applescript(mocker):
    """Test play falls back to AppleScript when MusicKit not configured."""
    mocker.patch.dict('os.environ', {}, clear=True)
    for key in ['APPLE_MUSIC_KEY_ID', 'APPLE_MUSIC_TEAM_ID', 'APPLE_MUSIC_PRIVATE_KEY', 'APPLE_MUSIC_KEY_PATH']:
        mocker.patch.dict('os.environ', {key: ''}, clear=False)

    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "playing:Test Song"
    mock_run.return_value.stderr = ""

    from xlg.commands.sinks import cmd_play
    result = cmd_play("Beatles")

    assert mock_run.call_args_list[0][0][0][0] == "osascript"
    assert "Playing: Test Song" in result
```

**Step 2: Run test**

Run: `uv run pytest xlg/commands/sinks_test.py::test_cmd_play_falls_back_to_applescript -v`
Expected: PASS

**Step 3: Run all tests**

Run: `uv run pytest -q`
Expected: All tests pass

**Step 4: Commit**

```bash
git add xlg/commands/sinks_test.py
git commit -m "test: add fallback behavior test for play"
```

---

### Task 5: Update README with MusicKit setup

**Files:**
- Modify: `README.md`

**Step 1: Add MusicKit setup section**

Add after "## Summarize Setup" in README.md:

```markdown
## Play Setup (Apple Music Catalog)

To search and play from Apple Music catalog (not just your library), configure MusicKit:

1. Get credentials from [Apple Developer Portal](https://developer.apple.com/account/resources/authkeys/list):
   - Create a MusicKit identifier
   - Download the private key (`.p8` file)
   - Note your Key ID and Team ID

2. Set environment variables:

```bash
export APPLE_MUSIC_KEY_ID="your-key-id"
export APPLE_MUSIC_TEAM_ID="your-team-id"
export APPLE_MUSIC_KEY_PATH="~/.config/xlg/AuthKey.p8"
```

Without these, `play` searches your local library only.
```

**Step 2: Run tests**

Run: `uv run pytest -q`
Expected: All tests pass

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add MusicKit setup instructions"
```

---

### Task 6: Final verification and push

**Step 1: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 2: Run linter**

Run: `uv run ruff check xlg/`
Expected: No errors

**Step 3: Reinstall and test manually**

Run: `uv cache clean xlg && uv tool install --force .`
Expected: Installed successfully

**Step 4: Push**

```bash
git push
```

**Step 5: Test with real credentials (manual)**

Set your real Apple Developer credentials and run:
```bash
xlg 'play "Gorillaz Feel Good Inc"'
```
Expected: Music.app opens and plays the song
