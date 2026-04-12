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
