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
**Sinks:** `print`, `write`, `store`, `play`, `open`, `fill`
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

## Fill Setup (AI Form Filling)

Automate checkout forms using Claude AI.

1. Set API key:

```bash
export ANTHROPIC_API_KEY="your-key"
```

2. Create profile:

```bash
mkdir -p ~/.config/xlg/data
cat > ~/.config/xlg/data/profile.json << 'EOF'
{
  "name": "Your Name",
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "zip": "94102"
}
EOF
```

3. Add site aliases:

```bash
cat > ~/.config/xlg/data/sites.json << 'EOF'
{
  "amazon": "https://amazon.com/checkout"
}
EOF
```

4. Usage:

```bash
xlg 'fill "amazon"'           # fill form using alias
xlg 'fill "https://..."'      # fill form at URL
```

Browser opens, Claude analyzes the form, fields are filled. Review and submit manually.

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

AI-powered form filling plugin. Uses Claude to map profile data to form fields and Playwright for browser automation.

```bash
xlg 'fill "amazon"'  # fill form using site alias
xlg 'fill "https://example.com/form"'  # fill form using direct URL
```

Config files in `~/.config/xlg/data/`:
- `sites.json`: Site aliases `{"amazon": "https://..."}`
- `profile.json`: User data `{"name": "John", "zip": "90210"}`

## Development

```bash
just test   # run tests
just lint   # check code
just fmt    # format code
```
