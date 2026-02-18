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

# Play song (macOS) - searches Apple Music catalog
xlg 'play "Beatles Yesterday"'

# Play playlist
xlg 'play "80s rock playlist"'

# Playback controls
xlg pause
xlg resume
xlg toggle
xlg skip
xlg previous
xlg 'volume 50'
xlg status
xlg favorite

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

## Play Setup

Music playback uses [xlg-player](../xlg-player). See its README for setup instructions.

## Plugin System

XLG supports custom commands via plugins. The `Registry` class stores source, transform, and sink functions.

```python
from xlg.plugins import Registry

registry = Registry()
registry.add_source("custom", lambda arg: iter([{"data": arg}]))
registry.add_transform("custom", lambda stream, arg: (x for x in stream))
registry.add_sink("custom", lambda data, arg: print(data))
```

### Fill Plugin

AI-powered form filling plugin with config loading:

```python
from xlg.plugins.fill import load_sites, load_profile, resolve_target

sites = load_sites(Path("~/.xlg/sites.json"))  # {"amazon": "https://..."}
profile = load_profile(Path("~/.xlg/profile.json"))  # {"name": "John", ...}
url = resolve_target("amazon", sites_path)  # resolves alias to URL
```

## Development

```bash
just test   # run tests
just lint   # check code
just fmt    # format code
```
