# XLG MCP Server Design

## Problem

The xlg author forgets command syntax between sessions and frequently operates through OpenClaw (AI chat agent) rather than a terminal. The CLI's pipe syntax is powerful but not memorable, and there's no way for AI agents to discover or invoke xlg commands programmatically.

## Solution

An MCP (Model Context Protocol) server that exposes xlg commands as typed, discoverable tools. AI agents call structured tools instead of constructing pipe expression strings.

## Architecture

```
OpenClaw / Claude Desktop / any MCP client
       │
       │ MCP (stdio transport)
       ▼
xlg-mcp-server (xlg/mcp_server.py)
       │
       │ direct function calls
       ▼
xlg command functions (sources, transforms, sinks, plugins)
```

- **Transport:** stdio — client spawns and manages the process lifecycle
- **Location:** `xlg/xlg/mcp_server.py` inside existing package
- **Entry point:** `xlg-mcp` CLI command via pyproject.toml `[project.scripts]`
- **Dependencies:** `mcp` Python SDK (only new dependency)

## Tools (10 total)

### Discovery (5 tools)

Each returns a list of `{title, url, description}` dicts.

| Tool | Params | Description |
|------|--------|-------------|
| `xlg_reddit` | `subreddit: str`, `query?: str`, `limit?: int=5` | Browse Reddit posts |
| `xlg_hn` | `query: str`, `limit?: int=5` | Browse Hacker News stories |
| `xlg_museum` | `query: str`, `limit?: int=5` | Browse Met Museum artworks |
| `xlg_github` | `query: str`, `limit?: int=5` | Search GitHub repositories |
| `xlg_wiki` | `query?: str`, `limit?: int=5` | Browse Wikipedia articles |

### Media (2 tools)

| Tool | Params | Description |
|------|--------|-------------|
| `xlg_play` | `query: str` | Play music via Apple Music |
| `xlg_playback` | `action: enum(pause,resume,toggle,skip,previous,status,favorite)`, `level?: str` | Playback controls |

### Data (2 tools)

| Tool | Params | Description |
|------|--------|-------------|
| `xlg_fetch` | `url: str`, `format?: enum(json,csv,rss)`, `field?: str`, `filter_field?: str`, `filter_value?: str`, `limit?: int` | Fetch URL, optionally parse/filter/take |
| `xlg_fill` | `target: str` | AI-assisted web form filling |

### Escape Hatch (1 tool)

| Tool | Params | Description |
|------|--------|-------------|
| `xlg_pipeline` | `expression: str` | Run arbitrary xlg pipe expression |

## Implementation

Single file `xlg/xlg/mcp_server.py` (~120 lines). Each tool is a function decorated with `@server.tool()` that calls existing `cmd_*` functions directly.

Discovery tools follow the pattern:
```python
@server.tool()
def xlg_reddit(subreddit: str, query: str = "", limit: int = 5) -> list[dict]:
    """Browse Reddit posts."""
    stream = cmd_reddit(subreddit, query)
    return list(cmd_take(stream, limit))
```

`xlg_fetch` builds pipeline incrementally from optional params:
```python
@server.tool()
def xlg_fetch(url: str, format: str = None, field: str = None,
              filter_field: str = None, filter_value: str = None, limit: int = None) -> list:
    """Fetch URL and optionally parse, filter, take."""
    stream = cmd_fetch(url)
    if format:
        stream = cmd_parse(stream, format)
    if field:
        stream = cmd_get(stream, field)
    if filter_field and filter_value:
        stream = cmd_filter(stream, filter_field, filter_value)
    if limit:
        stream = cmd_take(stream, limit)
    return list(stream)
```

`xlg_pipeline` reuses the existing lexer/parser/evaluator:
```python
@server.tool()
def xlg_pipeline(expression: str) -> list:
    """Run arbitrary xlg pipe expression."""
    return evaluate(parse(lex(expression)))
```

## Changes Required

| File | Change |
|------|--------|
| `xlg/xlg/mcp_server.py` | New file — MCP server with 10 tools |
| `xlg/pyproject.toml` | Add `mcp` dependency, add `xlg-mcp` script entry point |

## Client Configuration

Register in OpenClaw (or any MCP client) config:
```json
{
  "mcpServers": {
    "xlg": {
      "command": "xlg-mcp",
      "args": []
    }
  }
}
```

No manual start/stop — client manages server lifecycle via stdio.
