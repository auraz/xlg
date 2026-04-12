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
