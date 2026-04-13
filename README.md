# XLG - eXpression LanGuage

**Express complex operations in single commands.** Unix pipes for the modern web.

![xlg demo](assets/demo.gif)

Browse Reddit, Hacker News, Wikipedia, GitHub, Met Museum — or fetch any API — all from your terminal or AI agent.

## Quick Examples

```bash
xlg 'reddit "r/Art" | take 5'              # Top posts from r/Art
xlg 'hn "AI agents" | take 3'              # Hacker News stories
xlg 'museum "monet" | take 3'              # Met Museum artworks
xlg 'github "language:rust cli" | take 3'  # GitHub repos
xlg 'wiki "impressionism" | take 3'        # Wikipedia articles
xlg 'play "Debussy"'                       # Play on Apple Music
```

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

# Fill web form (prompts for missing fields)
xlg 'fill "https://shop.com/checkout"'
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

Automate web forms using Claude AI + Playwright.

1. Set API key:

```bash
export ANTHROPIC_API_KEY="your-key"
```

2. Usage:

```bash
xlg 'fill "https://example.com/form"'  # fill form at URL
xlg 'fill "amazon"'                     # fill form using alias
```

**How it works:**
1. Opens browser and navigates to URL
2. Claude analyzes form fields
3. Prompts for missing field values (values from profile/saved data are used automatically)
4. Fills the form
5. Auto-submits simple forms (≤3 fields like login) and continues to next form
6. Waits for you to review and submit complex forms manually

**Optional: Pre-fill common values**

Create `~/.config/xlg/data/profile.json` with values you use often:

```json
{"name": "Your Name", "country": "USA", "email": "you@example.com"}
```

Fields matching your profile are auto-filled; missing fields are prompted.

**Optional: Site aliases**

Create `~/.config/xlg/data/sites.json` for shortcuts:

```json
{"amazon": "https://amazon.com/checkout", "shop": "https://myshop.com/order"}
```

Then use: `xlg 'fill "amazon"'`

## Plugin System

Add custom commands via plugins in `~/.config/xlg/plugins/`:

```python
# ~/.config/xlg/plugins/hello.py
def register(registry):
    registry.add_sink("hello", lambda data, name: print(f"Hello, {name}!"))
```

```bash
xlg 'hello "World"'  # prints: Hello, World!
```

**Registry methods:** `add_source`, `add_transform`, `add_sink`

## MCP Server

Use xlg from AI agents (OpenClaw, Claude Desktop) via Model Context Protocol.

```bash
xlg-mcp  # starts MCP server (stdio transport)
```

### Setup

Add to your MCP client config:

**OpenClaw:**
```bash
openclaw mcp set xlg '{"command": "xlg-mcp"}'
openclaw gateway restart
```

**Claude Desktop / Other MCP clients:**
```json
{
  "mcpServers": {
    "xlg": {
      "command": "xlg-mcp"
    }
  }
}
```

Now your AI agent can browse Reddit, search GitHub, play music, and more — just by asking.

### Tools

| Tool | Description | Example |
|------|-------------|--------|
| `xlg_reddit` | Browse Reddit posts by subreddit | `subreddit="r/Art" query="monet" limit=5` |
| `xlg_hn` | Browse Hacker News (tech, startups, science) | `query="AI agents" limit=5` |
| `xlg_museum` | Search Met Museum collection (art!) | `query="impressionist" limit=5` |
| `xlg_github` | Search GitHub repos (supports search syntax) | `query="language:python mcp" limit=5` |
| `xlg_wiki` | Browse Wikipedia (empty query = random) | `query="" limit=5` |
| `xlg_play` | Play music on Apple Music (macOS) | `query="Debussy Clair de Lune"` |
| `xlg_playback` | Control playback | `action="pause\|skip\|volume" level="50"` |
| `xlg_fetch` | Fetch URL + chain operations | `url, format, field, filter_field, limit` |
| `xlg_fill` | AI form filling with Playwright | `target="https://..." or alias` |
| `xlg_pipeline` | Run full pipe expression | `expression="fetch ... \| parse ..."` |

## Development

```bash
just test   # run tests
just lint   # check code
just fmt    # format code
```
