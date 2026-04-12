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
    """Browse Reddit posts. Good for trending discussions, opinions, community content. Pass subreddit like 'r/Art' or 'r/python'. Optional query filters within the subreddit."""
    return list(cmd_take(cmd_reddit(subreddit, query), limit))


@mcp.tool()
def xlg_hn(query: str, limit: int = 5) -> list[dict]:
    """Browse Hacker News stories. Best for tech news, programming, startups, science. Returns top stories matching the query with links."""
    return list(cmd_take(cmd_hn(query), limit))


@mcp.tool()
def xlg_museum(query: str, limit: int = 5) -> list[dict]:
    """Browse Metropolitan Museum of Art collection. Search by artist ('monet'), style ('impressionist'), medium ('sculpture'), or subject ('landscape'). Returns artwork titles and links."""
    return list(cmd_take(cmd_museum("met", query), limit))


@mcp.tool()
def xlg_github(query: str, limit: int = 5) -> list[dict]:
    """Search GitHub repositories. Use GitHub search syntax: 'language:rust cli', 'topic:machine-learning', 'stars:>1000'. Returns repos sorted by stars."""
    return list(cmd_take(cmd_github(query), limit))


@mcp.tool()
def xlg_wiki(query: str = "", limit: int = 5) -> list[dict]:
    """Browse Wikipedia articles. Good for encyclopedic knowledge, facts, history. Empty query returns random articles for serendipitous discovery."""
    return list(cmd_take(cmd_wiki(query), limit))


@mcp.tool()
def xlg_play(query: str) -> str:
    """Play music on Apple Music (macOS only). Search by song ('Yesterday'), artist ('Beatles'), or playlist ('80s rock playlist'). Starts playback immediately."""
    return cmd_play(query)


@mcp.tool()
def xlg_playback(action: str, level: str = "") -> str:
    """Control music playback. Use after xlg_play. Actions: pause, resume, toggle (play/pause), skip (next track), previous, status (now playing as JSON), favorite (add to library), volume. For volume pass level: '50' (absolute), '+10'/'-10' (relative)."""
    actions = {"pause": cmd_pause, "resume": cmd_resume, "toggle": cmd_toggle, "skip": cmd_skip, "previous": cmd_previous, "status": cmd_status, "favorite": cmd_favorite}
    if action == "volume":
        return cmd_volume(level)
    if action not in actions:
        raise ValueError(f"Unknown action: {action}. Use: {', '.join(actions)}, volume")
    return actions[action]()


@mcp.tool()
def xlg_fetch(url: str, format: str = "", field: str = "", filter_field: str = "", filter_value: str = "", limit: int = 0) -> list:
    """Fetch any URL and process the response. Chain operations: parse (json/csv/rss), extract a nested field by dot-path, filter rows by field value, limit results. Example: fetch API, parse json, extract 'data.items', filter 'status'='active', limit 10."""
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
    """Fill a web form using AI (Claude + Playwright). Pass a URL or site alias. Opens browser, analyzes fields, prompts for missing values, fills and submits. Aliases configured in ~/.config/xlg/data/sites.json."""
    from xlg.plugins.fill import cmd_fill
    return cmd_fill(None, target)


@mcp.tool()
def xlg_pipeline(expression: str) -> list:
    """Run any xlg pipe expression when other tools don't cover your use case. Pipe syntax: 'source | transform | sink'. Example: 'read "data.csv" | parse csv | filter "region" "west" | sort "revenue" | take 10 | print'. See xlg README for full command list."""
    result = evaluate(parse(tokenize(expression)))
    return result if isinstance(result, list) else [result]


def main() -> None:
    """Entry point for xlg-mcp CLI."""
    mcp.run()
