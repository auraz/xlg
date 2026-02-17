# XLG - eXpression LanGuage

Express complex operations in single commands.

## Install

```bash
uv tool install xlg
```

## Usage

```bash
xlg 'fetch "api/users" | parse json | print'
```

```
┌───────────┐    ┌───────────┐    ┌───────────┐
│   fetch   │───▶│   parse   │───▶│   print   │
│  (source) │    │(transform)│    │   (sink)  │
└───────────┘    └───────────┘    └───────────┘
```

Or interactive REPL:

```bash
xlg
xlg> read "data.csv" | parse csv | filter "active" "true" | print
```

## Commands

**Sources:** `fetch`, `read`, `reddit`, `hn`, `museum`, `github`, `wiki`
**Transforms:** `parse` (json, csv, rss), `get`, `filter`, `sort`, `take`, `summarize`
**Sinks:** `print`, `write`, `store`, `play`, `open`
**Controls:** `pause`, `resume`, `toggle`, `skip`, `previous`, `volume`, `status`, `favorite`

## Examples

```bash
# API to database
xlg 'fetch "api/users" | parse json | store "users.db"'

# CSV filtering
xlg 'read "data.csv" | parse csv | filter "region" "west" | print'

# JSON extraction
xlg 'fetch "api/data" | parse json | get "items" | take 10 | print'

# Summarize text
xlg 'read "article.txt" | summarize | print'

# Play song (macOS) - searches Apple Music catalog, auto-plays
xlg 'play "Beatles Yesterday"'

# Play playlist - include "playlist" in query
xlg 'play "dio essentials playlist"'

# Open URLs in browser
xlg 'fetch "api/links" | parse json | get "items" | open'

# Browse Reddit posts
xlg 'reddit "r/Art" "monet" | take 5 | open'

# Browse Hacker News
xlg 'hn "python" | take 5 | open'

# Browse Met Museum artworks
xlg 'museum "met" "monet" | take 5 | open'

# Parse RSS feeds
xlg 'fetch "https://feed.url/rss" | parse rss | take 3 | open'
```

## Discovery

Find and open interesting content:

```bash
xlg 'reddit "r/Art" "impressionist" | take 3 | open'
xlg 'hn "cli tool" | take 3 | open'
xlg 'museum "met" "monet" | take 2 | open'
xlg 'github "language:rust cli" | take 3 | open'
xlg 'wiki "artificial intelligence" | take 3 | open'
xlg 'wiki | open'  # random articles
```

## Summarize Setup

The `summarize` command uses OpenAI API. Set your API key:

```bash
export OPENAI_API_KEY="your-key"
```

## Play Setup (Apple Music Catalog)

To search and auto-play from Apple Music catalog:

1. Get credentials from [Apple Developer Portal](https://developer.apple.com/account/resources/authkeys/list):
   - Keys → + → Enable MusicKit → Download `.p8` file
   - Note your Key ID and Team ID

2. Create config file:

```bash
mkdir -p ~/.config/xlg
mv ~/Downloads/AuthKey_*.p8 ~/.config/xlg/AuthKey.p8
cat > ~/.config/xlg/config << 'EOF'
APPLE_MUSIC_KEY_ID=your-key-id
APPLE_MUSIC_TEAM_ID=your-team-id
APPLE_MUSIC_KEY_PATH=~/.config/xlg/AuthKey.p8
EOF
```

3. Install native player (macOS 14+):

```bash
cd swift-player
swift build -c release
mkdir -p XlgPlayer.app/Contents/MacOS
cp .build/release/xlg-player XlgPlayer.app/Contents/MacOS/
codesign --force --sign - XlgPlayer.app  # or use your Developer ID
cp -r XlgPlayer.app ~/Applications/
```

On first run, grant MusicKit authorization when prompted.

**Usage:**

```bash
xlg 'play "Daft Punk Around the World"'  # song
xlg 'play "80s rock playlist"'            # playlist (include "playlist" in query)
```

**Audio Quality:** Uses your System Settings → Music → Audio Quality settings (Lossless/Hi-Res if enabled).

**Playback Controls:**

```
   advancement          playback           volume
 ◀◀ previous          ⏸️ pause           🔊 volume 50
 ▶▶ skip              ▶️ resume          🔊 volume +10
                      ⏯️ toggle          🔉 volume -10
```

```bash
xlg pause            # pause playback
xlg resume           # resume playback
xlg toggle           # toggle play/pause
xlg skip             # next track
xlg previous         # previous track
xlg 'volume 50'      # set volume to 50%
xlg 'volume +10'     # increase volume by 10%
xlg 'volume -10'     # decrease volume by 10%
xlg status           # get JSON status
xlg favorite         # toggle love on current track
```

## Stream Deck Plugin

Control Apple Music from Elgato Stream Deck.

```
┌─────────────────────────────────────────────────────────────┐
│                     Stream Deck Layout                       │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────┤
│    ⏮️    │   ⏯️    │    ⏭️    │    🔉    │    🔊    │  ❤️  │
│ Previous │  Toggle  │   Next   │  Vol -   │  Vol +   │ Love │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────┘
```

**Install:**

```bash
cd streamdeck-plugin
npm install
npm run build
cp -r com.xlg.player.sdPlugin ~/Library/Application\ Support/com.elgato.StreamDeck/Plugins/
```

Restart Stream Deck app, find **"XLG Controls"** category in the right sidebar.

**Actions:**

| Button | Icon | Action | Notes |
|--------|------|--------|-------|
| Play/Pause | ▶️/⏸️ | Toggle playback | Shows track title |
| Next | ⏭️ | Skip to next | |
| Previous | ⏮️ | Previous track | |
| Volume Up | 🔊 | +10% volume | System volume |
| Volume Down | 🔉 | -10% volume | System volume |
| Favorite | ❤️ | Toggle love | Current track |

**Architecture:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Stream Deck │────▶│ XLG Player  │────▶│  MusicKit   │
│   Plugin    │     │   (Swift)   │     │  / Music    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │   Unix Socket     │   AppleScript
       │  /tmp/xlg-player  │   (playlists)
       │       .sock       │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│   XLG CLI   │     │  Volume /   │
│  (Python)   │     │   Status    │
└─────────────┘     └─────────────┘
```

## Development

```bash
just test   # run tests (unit + integration)
just lint   # check code
just fmt    # format code
```
