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
