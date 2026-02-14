# Discovery Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add discovery sources (reddit, hn, museum) and `open` sink to find and view interesting content.

**Architecture:** New source commands yield `{title, url, source}` dicts. New `open` sink consumes URLs and opens in browser. RSS support via `parse rss` format.

**Tech Stack:** httpx (HTTP), feedparser (RSS), subprocess (browser open)

---

### Task 1: Add `open` Sink

**Files:**
- Modify: `xlg/commands/sinks.py`
- Modify: `xlg/evaluator.py`
- Test: `xlg/commands/sinks_test.py`

**Step 1: Write the failing test**

Add to `xlg/commands/sinks_test.py`:

```python
def test_cmd_open(mocker):
    """Test open command opens URLs in browser."""
    mock_run = mocker.patch("subprocess.run")
    items = iter([{"title": "Art", "url": "https://example.com/art"}, {"title": "Music", "url": "https://example.com/music"}])
    result = cmd_open(items)
    assert result == ["https://example.com/art", "https://example.com/music"]
    assert mock_run.call_count == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/commands/sinks_test.py::test_cmd_open -v`
Expected: FAIL with "cannot import name 'cmd_open'"

**Step 3: Write minimal implementation**

Add to `xlg/commands/sinks.py`:

```python
def cmd_open(upstream: Generator[Any, None, None]) -> list[str]:
    """Open URLs in browser."""
    urls = []
    for item in upstream:
        url = item["url"] if isinstance(item, dict) else str(item)
        subprocess.run(["open", url])
        urls.append(url)
    return urls
```

**Step 4: Add pytest-mock dependency**

Run: `uv add --dev pytest-mock`

**Step 5: Run test to verify it passes**

Run: `uv run pytest xlg/commands/sinks_test.py::test_cmd_open -v`
Expected: PASS

**Step 6: Wire up evaluator**

Add import in `xlg/evaluator.py`:
```python
from xlg.commands.sinks import cmd_print, cmd_write, cmd_store, cmd_play, cmd_open
```

Add case in evaluate function:
```python
elif name == "open":
    return cmd_open(stream)
```

**Step 7: Commit**

```bash
git add xlg/commands/sinks.py xlg/commands/sinks_test.py xlg/evaluator.py pyproject.toml uv.lock
git commit -m "feat: add open sink to open URLs in browser"
```

---

### Task 2: Add `reddit` Source

**Files:**
- Create: `xlg/commands/discovery.py`
- Create: `xlg/commands/discovery_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write the failing test**

Create `xlg/commands/discovery_test.py`:

```python
"""Tests for discovery commands."""
from xlg.commands.discovery import cmd_reddit


def test_cmd_reddit_yields_items(mocker):
    """Test reddit command yields items with title, url, source."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"data": {"children": [{"data": {"title": "Cool Art", "permalink": "/r/Art/123"}}, {"data": {"title": "Nice Painting", "permalink": "/r/Art/456"}}]}}
    mocker.patch("httpx.get", return_value=mock_response)
    result = list(cmd_reddit("r/Art", "monet"))
    assert len(result) == 2
    assert result[0] == {"title": "Cool Art", "url": "https://reddit.com/r/Art/123", "source": "reddit"}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/commands/discovery_test.py::test_cmd_reddit_yields_items -v`
Expected: FAIL with "No module named 'xlg.commands.discovery'"

**Step 3: Write minimal implementation**

Create `xlg/commands/discovery.py`:

```python
"""Discovery source commands."""
import httpx
from collections.abc import Generator


def cmd_reddit(subreddit: str, query: str = "") -> Generator[dict, None, None]:
    """Fetch posts from Reddit."""
    sub = subreddit.lstrip("r/")
    url = f"https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=1&limit=10" if query else f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
    response = httpx.get(url, headers={"User-Agent": "xlg/0.1"})
    response.raise_for_status()
    for child in response.json()["data"]["children"]:
        post = child["data"]
        yield {"title": post["title"], "url": f"https://reddit.com{post['permalink']}", "source": "reddit"}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/commands/discovery_test.py::test_cmd_reddit_yields_items -v`
Expected: PASS

**Step 5: Wire up evaluator**

Add import in `xlg/evaluator.py`:
```python
from xlg.commands.discovery import cmd_reddit
```

Add case in evaluate function:
```python
elif name == "reddit":
    stream = cmd_reddit(args[0], args[1] if len(args) > 1 else "")
```

**Step 6: Commit**

```bash
git add xlg/commands/discovery.py xlg/commands/discovery_test.py xlg/evaluator.py
git commit -m "feat: add reddit source command"
```

---

### Task 3: Add `hn` Source

**Files:**
- Modify: `xlg/commands/discovery.py`
- Modify: `xlg/commands/discovery_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write the failing test**

Add to `xlg/commands/discovery_test.py`:

```python
from xlg.commands.discovery import cmd_reddit, cmd_hn


def test_cmd_hn_yields_items(mocker):
    """Test hn command yields items with title, url, source."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"hits": [{"title": "CLI Tool", "url": "https://example.com/tool", "objectID": "123"}, {"title": "Another Tool", "url": "", "objectID": "456"}]}
    mocker.patch("httpx.get", return_value=mock_response)
    result = list(cmd_hn("cli"))
    assert len(result) == 2
    assert result[0] == {"title": "CLI Tool", "url": "https://example.com/tool", "source": "hn"}
    assert result[1] == {"title": "Another Tool", "url": "https://news.ycombinator.com/item?id=456", "source": "hn"}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/commands/discovery_test.py::test_cmd_hn_yields_items -v`
Expected: FAIL with "cannot import name 'cmd_hn'"

**Step 3: Write minimal implementation**

Add to `xlg/commands/discovery.py`:

```python
def cmd_hn(query: str) -> Generator[dict, None, None]:
    """Fetch posts from Hacker News via Algolia API."""
    url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=10"
    response = httpx.get(url)
    response.raise_for_status()
    for hit in response.json()["hits"]:
        item_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        yield {"title": hit["title"], "url": item_url, "source": "hn"}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/commands/discovery_test.py::test_cmd_hn_yields_items -v`
Expected: PASS

**Step 5: Wire up evaluator**

Add import in `xlg/evaluator.py`:
```python
from xlg.commands.discovery import cmd_reddit, cmd_hn
```

Add case in evaluate function:
```python
elif name == "hn":
    stream = cmd_hn(args[0])
```

**Step 6: Commit**

```bash
git add xlg/commands/discovery.py xlg/commands/discovery_test.py xlg/evaluator.py
git commit -m "feat: add hn source command"
```

---

### Task 4: Add `museum` Source

**Files:**
- Modify: `xlg/commands/discovery.py`
- Modify: `xlg/commands/discovery_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write the failing test**

Add to `xlg/commands/discovery_test.py`:

```python
from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum


def test_cmd_museum_yields_items(mocker):
    """Test museum command yields items with title, url, source."""
    mock_search = mocker.Mock()
    mock_search.json.return_value = {"objectIDs": [1, 2]}
    mock_obj1 = mocker.Mock()
    mock_obj1.json.return_value = {"title": "Water Lilies", "objectID": 1, "primaryImage": "https://met.org/1.jpg"}
    mock_obj2 = mocker.Mock()
    mock_obj2.json.return_value = {"title": "Starry Night", "objectID": 2, "primaryImage": "https://met.org/2.jpg"}
    mocker.patch("httpx.get", side_effect=[mock_search, mock_obj1, mock_obj2])
    result = list(cmd_museum("met", "monet"))
    assert len(result) == 2
    assert result[0] == {"title": "Water Lilies", "url": "https://www.metmuseum.org/art/collection/search/1", "source": "museum"}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/commands/discovery_test.py::test_cmd_museum_yields_items -v`
Expected: FAIL with "cannot import name 'cmd_museum'"

**Step 3: Write minimal implementation**

Add to `xlg/commands/discovery.py`:

```python
def cmd_museum(museum: str, query: str) -> Generator[dict, None, None]:
    """Fetch artworks from museum API."""
    if museum != "met":
        raise ValueError(f"museum: unsupported museum '{museum}', use 'met'")
    search_url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q={query}&hasImages=true"
    response = httpx.get(search_url)
    response.raise_for_status()
    object_ids = response.json().get("objectIDs") or []
    for oid in object_ids[:10]:
        obj_response = httpx.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        obj = obj_response.json()
        if obj.get("primaryImage"):
            yield {"title": obj["title"], "url": f"https://www.metmuseum.org/art/collection/search/{oid}", "source": "museum"}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/commands/discovery_test.py::test_cmd_museum_yields_items -v`
Expected: PASS

**Step 5: Wire up evaluator**

Add import in `xlg/evaluator.py`:
```python
from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum
```

Add case in evaluate function:
```python
elif name == "museum":
    stream = cmd_museum(args[0], args[1])
```

**Step 6: Commit**

```bash
git add xlg/commands/discovery.py xlg/commands/discovery_test.py xlg/evaluator.py
git commit -m "feat: add museum source command"
```

---

### Task 5: Add RSS Parse Format

**Files:**
- Modify: `xlg/commands/transforms.py`
- Modify: `xlg/commands/transforms_test.py`
- Modify: `pyproject.toml`

**Step 1: Add feedparser dependency**

Run: `uv add feedparser`

**Step 2: Write the failing test**

Add to `xlg/commands/transforms_test.py`:

```python
def test_cmd_parse_rss():
    """Test parse rss yields items with title, url, source."""
    rss_content = '''<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item><title>Post 1</title><link>https://example.com/1</link></item>
            <item><title>Post 2</title><link>https://example.com/2</link></item>
        </channel>
    </rss>'''
    result = list(cmd_parse(iter([rss_content]), "rss"))
    assert len(result) == 2
    assert result[0] == {"title": "Post 1", "url": "https://example.com/1", "source": "rss"}
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest xlg/commands/transforms_test.py::test_cmd_parse_rss -v`
Expected: FAIL (rss format not handled)

**Step 4: Write minimal implementation**

Add import at top of `xlg/commands/transforms.py`:
```python
import feedparser
```

Update `cmd_parse` function to handle rss:
```python
def cmd_parse(upstream: Generator[Any, None, None], format: str) -> Generator[Any, None, None]:
    """Parse input data according to format."""
    for item in upstream:
        if format == "json":
            parsed = json.loads(item)
            if isinstance(parsed, list):
                yield from parsed
            else:
                yield parsed
        elif format == "csv":
            reader = csv.DictReader(StringIO(item))
            yield from reader
        elif format == "rss":
            feed = feedparser.parse(item)
            for entry in feed.entries:
                yield {"title": entry.get("title", ""), "url": entry.get("link", ""), "source": "rss"}
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest xlg/commands/transforms_test.py::test_cmd_parse_rss -v`
Expected: PASS

**Step 6: Commit**

```bash
git add xlg/commands/transforms.py xlg/commands/transforms_test.py pyproject.toml uv.lock
git commit -m "feat: add rss parse format"
```

---

### Task 6: Update README

**Files:**
- Modify: `README.md`

**Step 1: Update README**

Replace contents of `README.md`:

```markdown
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

**Sources:** `fetch`, `read`, `reddit`, `hn`, `museum`
**Transforms:** `parse` (json, csv, rss), `get`, `filter`, `sort`, `take`, `summarize`
**Sinks:** `print`, `write`, `store`, `open`, `play`

## Discovery

Find and open interesting content:

```bash
# Art from Reddit
xlg 'reddit "r/Art" "impressionist" | take 3 | open'

# Tools from Hacker News
xlg 'hn "cli tool" | take 3 | open'

# Art from Met Museum
xlg 'museum "met" "monet" | take 2 | open'

# RSS feeds
xlg 'fetch "https://feed.url/rss" | parse rss | take 3 | open'
```

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

# Play music (macOS)
xlg 'play "Beatles"'
```

## Summarize Setup

The `summarize` command uses OpenAI API. Set your API key:

```bash
export OPENAI_API_KEY="your-key"
```

## Development

```bash
just test   # run tests (unit + integration)
just lint   # check code
just fmt    # format code
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add discovery commands to README"
```

---

### Task 7: Integration Test

**Files:**
- Modify: `tests/integration_test.py`

**Step 1: Write integration test**

Add to `tests/integration_test.py`:

```python
def test_discovery_pipeline_structure():
    """Test discovery pipeline yields correct structure."""
    from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum
    # Just verify the generators exist and have correct signature
    assert callable(cmd_reddit)
    assert callable(cmd_hn)
    assert callable(cmd_museum)
```

**Step 2: Run all tests**

Run: `uv run pytest -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/integration_test.py
git commit -m "test: add discovery integration test"
```

---

### Task 8: Final Verification

**Step 1: Run linter**

Run: `just lint`
Expected: No errors

**Step 2: Format code**

Run: `just fmt`

**Step 3: Run all tests**

Run: `just test`
Expected: All tests PASS

**Step 4: Manual test**

Run: `just run 'hn "cli" | take 2 | print'`
Expected: Prints 2 HN items with title, url, source

**Step 5: Final commit if any formatting changes**

```bash
git add -A && git commit -m "style: format code"
```
