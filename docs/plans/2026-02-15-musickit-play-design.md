# MusicKit Play Command Design

## Goal

Enable `play` command to search and play any song from Apple Music catalog, not just local library.

## Architecture

```
play "Gorillaz"
    → MusicKit API search → song ID
    → open music://.../{id} → Music.app plays
```

## Credentials

Environment variables:
- `APPLE_MUSIC_KEY_ID` - MusicKit key identifier
- `APPLE_MUSIC_TEAM_ID` - Apple Developer team ID
- `APPLE_MUSIC_PRIVATE_KEY` - Private key content (PEM format)
- `APPLE_MUSIC_KEY_PATH` - Alternative: path to `.p8` file

## Dependencies

- `apple-music-python` - Python wrapper for Apple Music API

## Implementation

1. Load credentials from environment
2. Create AppleMusic client with JWT auth
3. Search catalog: `am.search(query, types=['songs'], limit=1)`
4. Extract song ID from first result
5. Open URL: `subprocess.run(["open", f"music://music.apple.com/us/song/{song_id}"])`

## Error Handling

- Missing credentials → clear error message with setup instructions
- No search results → raise "No songs found for: {query}"
- API errors → surface Apple Music API error message

## Fallback

If MusicKit credentials not configured, fall back to current behavior (library search + URL fallback).
