# XLG Discovery Feature Design

Personal discovery assistant — find and open interesting content on-demand.

## Goal

Add composable source commands for content discovery, plus an `open` sink to view results in browser.

## Usage Examples

```bash
xlg 'reddit "r/Art" "impressionist" | take 3 | open'
xlg 'hn "cli tool" | take 3 | open'
xlg 'museum "met" "monet" | take 2 | open'
xlg 'fetch "https://feed.url/rss" | parse rss | take 3 | open'
```

## New Source Commands

| Command | Usage | API |
|---------|-------|-----|
| `reddit` | `reddit "r/Art" "monet"` | Reddit JSON API (no auth) |
| `hn` | `hn "cli"` | Algolia HN Search API |
| `museum` | `museum "met" "impressionist"` | Met Museum API (free) |

Output format (consistent across all):
```python
{"title": "...", "url": "...", "source": "reddit"}
```

## New `open` Sink

Opens URLs in default browser via macOS `open` command.

```python
def cmd_open(upstream: Generator) -> list[str]:
    """Open URLs in browser."""
    urls = []
    for item in upstream:
        url = item["url"] if isinstance(item, dict) else str(item)
        subprocess.run(["open", url])
        urls.append(url)
    return urls
```

## RSS Support

Add `rss` as parse format using `feedparser` library:

```bash
xlg 'fetch "https://feed.url/rss" | parse rss | take 3 | open'
```

Output matches other sources: `{"title": "...", "url": "...", "source": "rss"}`.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Network error | Raise: `"reddit: connection failed"` |
| No results | Yield nothing (empty generator) |
| Invalid subreddit | Raise: `"reddit: r/FakeSubreddit not found"` |
| Rate limited | Raise: `"hn: rate limited, try again"` |

No fallbacks, no retries — fail fast.

## README Updates

Update commands list and add discovery examples section.
