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

Or interactive REPL:

```bash
xlg
xlg> read "data.csv" | parse csv | filter "active" "true" | print
```

## Commands

**Sources:** `fetch`, `read`, `reddit`, `hn`, `museum`, `github`, `wiki`
**Transforms:** `parse` (json, csv, rss), `get`, `filter`, `sort`, `take`, `summarize`
**Sinks:** `print`, `write`, `store`, `play`, `open`

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

# Play music (macOS) - library first, then opens catalog search
xlg 'play "Beatles"'

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

To search and play from Apple Music catalog (not just your library), configure MusicKit:

1. Get credentials from [Apple Developer Portal](https://developer.apple.com/account/resources/authkeys/list):
   - Create a MusicKit identifier
   - Download the private key (`.p8` file)
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

Without these, `play` searches your local library only.

## Development

```bash
just test   # run tests (unit + integration)
just lint   # check code
just fmt    # format code
```
