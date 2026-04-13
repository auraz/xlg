# XLG MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose xlg commands as typed MCP tools so AI agents (OpenClaw, Claude Desktop) can invoke them without knowing pipe syntax.

**Architecture:** Single `mcp_server.py` module using FastMCP, importing existing `cmd_*` functions directly. stdio transport, client-managed lifecycle. Entry point `xlg-mcp` registered in pyproject.toml.

**Tech Stack:** Python 3.14, `mcp` SDK (FastMCP), existing xlg command functions.

---

### Task 1: Add mcp dependency and entry point

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add mcp to dependencies**

In `pyproject.toml`, add `"mcp>=1.0"` to the `dependencies` list:

```toml
dependencies = [
    "feedparser>=6.0.12",
    "httpx>=0.27",
    "openai>=2.21.0",
    "xlg-player",
    "playwright>=1.40",
    "anthropic>=0.40",
    "mcp>=1.0",
]
```

- [ ] **Step 2: Add xlg-mcp script entry point**

In `pyproject.toml`, update `[project.scripts]`:

```toml
[project.scripts]
xlg = "xlg.main:main"
xlg-mcp = "xlg.mcp_server:main"
```

- [ ] **Step 3: Install updated dependencies**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv sync`
Expected: mcp package installed successfully.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add mcp dependency and xlg-mcp entry point"
```

---

### Task 2: Create MCP server with discovery tools

**Files:**
- Create: `xlg/xlg/mcp_server.py`
- Test: `xlg/xlg/mcp_server_test.py`

- [ ] **Step 1: Write failing tests for discovery tools**

Create `xlg/xlg/mcp_server_test.py`:

```python
"""MCP server tests."""

from unittest.mock import patch, MagicMock
from xlg.mcp_server import xlg_reddit, xlg_hn, xlg_museum, xlg_github, xlg_wiki


def _make_posts(n: int) -> list[dict]:
    """Generate fake discovery posts."""
    return [{"title": f"Post {i}", "url": f"https://example.com/{i}", "source": "test"} for i in range(n)]


def _gen(items):
    """Turn list into generator."""
    yield from items


@patch("xlg.mcp_server.cmd_reddit")
def test_xlg_reddit(mock_reddit):
    mock_reddit.return_value = _gen(_make_posts(10))
    result = xlg_reddit("r/python", query="fastapi", limit=3)
    mock_reddit.assert_called_once_with("r/python", "fastapi")
    assert len(result) == 3


@patch("xlg.mcp_server.cmd_reddit")
def test_xlg_reddit_defaults(mock_reddit):
    mock_reddit.return_value = _gen(_make_posts(10))
    result = xlg_reddit("r/Art")
    mock_reddit.assert_called_once_with("r/Art", "")
    assert len(result) == 5


@patch("xlg.mcp_server.cmd_hn")
def test_xlg_hn(mock_hn):
    mock_hn.return_value = _gen(_make_posts(10))
    result = xlg_hn("python", limit=2)
    mock_hn.assert_called_once_with("python")
    assert len(result) == 2


@patch("xlg.mcp_server.cmd_museum")
def test_xlg_museum(mock_museum):
    mock_museum.return_value = _gen(_make_posts(10))
    result = xlg_museum("monet", limit=3)
    mock_museum.assert_called_once_with("met", "monet")
    assert len(result) == 3


@patch("xlg.mcp_server.cmd_github")
def test_xlg_github(mock_github):
    mock_github.return_value = _gen(_make_posts(10))
    result = xlg_github("language:rust cli", limit=4)
    mock_github.assert_called_once_with("language:rust cli")
    assert len(result) == 4


@patch("xlg.mcp_server.cmd_wiki")
def test_xlg_wiki(mock_wiki):
    mock_wiki.return_value = _gen(_make_posts(10))
    result = xlg_wiki(query="AI", limit=3)
    mock_wiki.assert_called_once_with("AI")
    assert len(result) == 3


@patch("xlg.mcp_server.cmd_wiki")
def test_xlg_wiki_random(mock_wiki):
    mock_wiki.return_value = _gen(_make_posts(5))
    result = xlg_wiki()
    mock_wiki.assert_called_once_with("")
    assert len(result) == 5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py -v`
Expected: FAIL — `mcp_server` module does not exist.

- [ ] **Step 3: Implement MCP server with discovery tools**

Create `xlg/xlg/mcp_server.py`:

```python
"""XLG MCP server — exposes xlg commands as MCP tools."""

from mcp.server.fastmcp import FastMCP
from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum, cmd_github, cmd_wiki
from xlg.commands.transforms import cmd_take

mcp = FastMCP("xlg")


@mcp.tool()
def xlg_reddit(subreddit: str, query: str = "", limit: int = 5) -> list[dict]:
    """Browse Reddit posts from a subreddit, optionally filtered by search query."""
    return list(cmd_take(cmd_reddit(subreddit, query), limit))


@mcp.tool()
def xlg_hn(query: str, limit: int = 5) -> list[dict]:
    """Browse Hacker News stories matching a search query."""
    return list(cmd_take(cmd_hn(query), limit))


@mcp.tool()
def xlg_museum(query: str, limit: int = 5) -> list[dict]:
    """Browse Met Museum artworks matching a search query."""
    return list(cmd_take(cmd_museum("met", query), limit))


@mcp.tool()
def xlg_github(query: str, limit: int = 5) -> list[dict]:
    """Search GitHub repositories."""
    return list(cmd_take(cmd_github(query), limit))


@mcp.tool()
def xlg_wiki(query: str = "", limit: int = 5) -> list[dict]:
    """Browse Wikipedia articles. Empty query returns random articles."""
    return list(cmd_take(cmd_wiki(query), limit))


def main() -> None:
    """Entry point for xlg-mcp CLI."""
    mcp.run()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add xlg/mcp_server.py xlg/mcp_server_test.py
git commit -m "feat: add MCP server with discovery tools"
```

---

### Task 3: Add media tools (play, playback)

**Files:**
- Modify: `xlg/xlg/mcp_server.py`
- Modify: `xlg/xlg/mcp_server_test.py`

- [ ] **Step 1: Write failing tests for media tools**

Append to `xlg/xlg/mcp_server_test.py`:

```python
from xlg.mcp_server import xlg_play, xlg_playback


@patch("xlg.mcp_server.cmd_play")
def test_xlg_play(mock_play):
    mock_play.return_value = "Playing: Beatles Yesterday"
    result = xlg_play("Beatles Yesterday")
    mock_play.assert_called_once_with("Beatles Yesterday")
    assert result == "Playing: Beatles Yesterday"


@patch("xlg.mcp_server.cmd_toggle")
def test_xlg_playback_toggle(mock_toggle):
    mock_toggle.return_value = "toggled"
    result = xlg_playback("toggle")
    mock_toggle.assert_called_once()
    assert result == "toggled"


@patch("xlg.mcp_server.cmd_volume")
def test_xlg_playback_volume(mock_volume):
    mock_volume.return_value = "volume: 50"
    result = xlg_playback("volume", level="50")
    mock_volume.assert_called_once_with("50")
    assert result == "volume: 50"


@patch("xlg.mcp_server.cmd_pause")
def test_xlg_playback_pause(mock_pause):
    mock_pause.return_value = "paused"
    result = xlg_playback("pause")
    mock_pause.assert_called_once()
    assert result == "paused"


@patch("xlg.mcp_server.cmd_skip")
def test_xlg_playback_skip(mock_skip):
    mock_skip.return_value = "skipped"
    result = xlg_playback("skip")
    mock_skip.assert_called_once()
    assert result == "skipped"
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py -v -k "play or playback"`
Expected: FAIL — `xlg_play` and `xlg_playback` not importable.

- [ ] **Step 3: Implement media tools**

Add to `xlg/xlg/mcp_server.py` — new imports at top:

```python
from xlg.commands.sinks import cmd_play, cmd_pause, cmd_resume, cmd_toggle, cmd_skip, cmd_previous, cmd_volume, cmd_status, cmd_favorite
```

Add tool functions before `main()`:

```python
@mcp.tool()
def xlg_play(query: str) -> str:
    """Play music on Apple Music. Search by song name, artist, or playlist."""
    return cmd_play(query)


@mcp.tool()
def xlg_playback(action: str, level: str = "") -> str:
    """Control music playback. Actions: pause, resume, toggle, skip, previous, status, favorite, volume. Pass level for volume (0-100, +10, -10)."""
    actions = {"pause": cmd_pause, "resume": cmd_resume, "toggle": cmd_toggle, "skip": cmd_skip, "previous": cmd_previous, "status": cmd_status, "favorite": cmd_favorite}
    if action == "volume":
        return cmd_volume(level)
    if action not in actions:
        raise ValueError(f"Unknown action: {action}. Use: {', '.join(actions)}, volume")
    return actions[action]()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py -v`
Expected: All 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add xlg/mcp_server.py xlg/mcp_server_test.py
git commit -m "feat: add play and playback MCP tools"
```

---

### Task 4: Add data tools (fetch, fill)

**Files:**
- Modify: `xlg/xlg/mcp_server.py`
- Modify: `xlg/xlg/mcp_server_test.py`

- [ ] **Step 1: Write failing tests for data tools**

Append to `xlg/xlg/mcp_server_test.py`:

```python
from xlg.mcp_server import xlg_fetch, xlg_fill


@patch("xlg.mcp_server.cmd_fetch")
def test_xlg_fetch_raw(mock_fetch):
    mock_fetch.return_value = _gen(["raw html"])
    result = xlg_fetch("https://example.com")
    mock_fetch.assert_called_once_with("https://example.com")
    assert result == ["raw html"]


@patch("xlg.mcp_server.cmd_parse")
@patch("xlg.mcp_server.cmd_fetch")
def test_xlg_fetch_json(mock_fetch, mock_parse):
    mock_fetch.return_value = _gen(['[{"a":1}]'])
    mock_parse.return_value = _gen([{"a": 1}])
    result = xlg_fetch("https://api.com/data", format="json")
    mock_parse.assert_called_once()
    assert result == [{"a": 1}]


@patch("xlg.mcp_server.cmd_get")
@patch("xlg.mcp_server.cmd_parse")
@patch("xlg.mcp_server.cmd_fetch")
def test_xlg_fetch_json_with_field(mock_fetch, mock_parse, mock_get):
    mock_fetch.return_value = _gen(['{"items":[1,2]}'])
    mock_parse.return_value = _gen([{"items": [1, 2]}])
    mock_get.return_value = _gen([1, 2])
    result = xlg_fetch("https://api.com", format="json", field="items")
    mock_get.assert_called_once()
    assert result == [1, 2]


@patch("xlg.mcp_server.cmd_filter")
@patch("xlg.mcp_server.cmd_parse")
@patch("xlg.mcp_server.cmd_fetch")
def test_xlg_fetch_with_filter(mock_fetch, mock_parse, mock_filter):
    mock_fetch.return_value = _gen(["csv"])
    mock_parse.return_value = _gen([{"active": "true"}, {"active": "false"}])
    mock_filter.return_value = _gen([{"active": "true"}])
    result = xlg_fetch("https://data.com", format="csv", filter_field="active", filter_value="true")
    mock_filter.assert_called_once()
    assert result == [{"active": "true"}]


@patch("xlg.mcp_server.cmd_fetch")
def test_xlg_fetch_with_limit(mock_fetch):
    mock_fetch.return_value = _gen(["a", "b", "c", "d", "e"])
    result = xlg_fetch("https://example.com", limit=2)
    assert len(result) == 2
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py -v -k "xlg_fetch or xlg_fill"`
Expected: FAIL — `xlg_fetch` and `xlg_fill` not importable.

- [ ] **Step 3: Implement data tools**

Add to `xlg/xlg/mcp_server.py` — new imports at top:

```python
from xlg.commands.sources import cmd_fetch
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter
```

Note: `cmd_take` is already imported. Add tool functions before `main()`:

```python
@mcp.tool()
def xlg_fetch(url: str, format: str = "", field: str = "", filter_field: str = "", filter_value: str = "", limit: int = 0) -> list:
    """Fetch URL content. Optionally parse (json/csv/rss), extract field, filter, and limit results."""
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


@mcp.tool()
def xlg_fill(target: str) -> str:
    """Fill a web form using AI. Pass a URL or site alias (e.g. 'amazon')."""
    from xlg.plugins.fill import cmd_fill
    return cmd_fill(None, target)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py -v`
Expected: All 17 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add xlg/mcp_server.py xlg/mcp_server_test.py
git commit -m "feat: add fetch and fill MCP tools"
```

---

### Task 5: Add pipeline escape hatch

**Files:**
- Modify: `xlg/xlg/mcp_server.py`
- Modify: `xlg/xlg/mcp_server_test.py`

- [ ] **Step 1: Write failing test for pipeline tool**

Append to `xlg/xlg/mcp_server_test.py`:

```python
import tempfile
from pathlib import Path
from xlg.mcp_server import xlg_pipeline


def test_xlg_pipeline():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('[{"name": "alice"}, {"name": "bob"}]')
        path = f.name
    result = xlg_pipeline(f'read "{path}" | parse json | take 1 | print')
    assert result == [{"name": "alice"}]
    Path(path).unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py::test_xlg_pipeline -v`
Expected: FAIL — `xlg_pipeline` not importable.

- [ ] **Step 3: Implement pipeline tool**

Add to `xlg/xlg/mcp_server.py` — new imports at top:

```python
from xlg.lexer import tokenize
from xlg.parser import parse
from xlg.evaluator import evaluate
```

Add tool function before `main()`:

```python
@mcp.tool()
def xlg_pipeline(expression: str) -> list:
    """Run an arbitrary xlg pipe expression. Example: 'fetch "api/users" | parse json | take 5 | print'"""
    result = evaluate(parse(tokenize(expression)))
    return result if isinstance(result, list) else [result]
```

- [ ] **Step 4: Run all tests to verify everything passes**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest xlg/mcp_server_test.py -v`
Expected: All 18 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add xlg/mcp_server.py xlg/mcp_server_test.py
git commit -m "feat: add pipeline escape hatch MCP tool"
```

---

### Task 6: Verify full server and update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run full test suite to confirm no regressions**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run pytest -v`
Expected: All existing tests + 18 new tests PASS.

- [ ] **Step 2: Run linter**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && uv run ruff check xlg/mcp_server.py xlg/mcp_server_test.py`
Expected: No errors. Fix any issues.

- [ ] **Step 3: Smoke test the MCP server starts**

Run: `cd /Users/ok/Documents/02-areas/career/repos/1.InDevelopment/XLGGroup/xlg && echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | uv run xlg-mcp 2>/dev/null | head -1`
Expected: JSON response with server capabilities (confirms server starts and responds to MCP protocol).

- [ ] **Step 4: Add MCP section to README.md**

Add after the "## Plugin System" section in `README.md`:

```markdown
## MCP Server

Use xlg from AI agents (OpenClaw, Claude Desktop) via Model Context Protocol.

```bash
xlg-mcp  # starts MCP server (stdio transport)
```

### Setup

Add to your MCP client config:

```json
{
  "mcpServers": {
    "xlg": {
      "command": "xlg-mcp"
    }
  }
}
```

### Tools

| Tool | Description |
|------|-------------|
| `xlg_reddit` | Browse Reddit posts |
| `xlg_hn` | Browse Hacker News stories |
| `xlg_museum` | Browse Met Museum artworks |
| `xlg_github` | Search GitHub repositories |
| `xlg_wiki` | Browse Wikipedia articles |
| `xlg_play` | Play music on Apple Music |
| `xlg_playback` | Playback controls (pause, skip, volume, etc.) |
| `xlg_fetch` | Fetch URL + parse/filter/limit |
| `xlg_fill` | AI-assisted web form filling |
| `xlg_pipeline` | Run arbitrary xlg pipe expression |
```

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add MCP server section to README"
```
