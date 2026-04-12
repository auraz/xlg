"""XLG MCP server — exposes xlg commands as MCP tools."""

from mcp.server.fastmcp import FastMCP
from xlg.lexer import tokenize
from xlg.parser import parse
from xlg.evaluator import evaluate
from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum, cmd_github, cmd_wiki
from xlg.commands.sinks import cmd_play, cmd_pause, cmd_resume, cmd_toggle, cmd_skip, cmd_previous, cmd_volume, cmd_status, cmd_favorite
from xlg.commands.transforms import cmd_take, cmd_parse, cmd_get, cmd_filter
from xlg.commands.sources import cmd_fetch

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


@mcp.tool()
def xlg_pipeline(expression: str) -> list:
    """Run an arbitrary xlg pipe expression. Example: 'fetch "api/users" | parse json | take 5 | print'"""
    result = evaluate(parse(tokenize(expression)))
    return result if isinstance(result, list) else [result]


def main() -> None:
    """Entry point for xlg-mcp CLI."""
    mcp.run()
