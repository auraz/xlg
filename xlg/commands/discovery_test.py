"""Tests for discovery commands."""
from xlg.commands.discovery import cmd_reddit, cmd_hn


def test_cmd_reddit_yields_items(mocker):
    """Test reddit command yields items with title, url, source."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"data": {"children": [{"data": {"title": "Cool Art", "permalink": "/r/Art/123"}}, {"data": {"title": "Nice Painting", "permalink": "/r/Art/456"}}]}}
    mocker.patch("httpx.get", return_value=mock_response)
    result = list(cmd_reddit("r/Art", "monet"))
    assert len(result) == 2
    assert result[0] == {"title": "Cool Art", "url": "https://reddit.com/r/Art/123", "source": "reddit"}


def test_cmd_hn_yields_items(mocker):
    """Test hn command yields items with title, url, source."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"hits": [{"title": "CLI Tool", "url": "https://example.com/tool", "objectID": "123"}, {"title": "Another Tool", "url": "", "objectID": "456"}]}
    mocker.patch("httpx.get", return_value=mock_response)
    result = list(cmd_hn("cli"))
    assert len(result) == 2
    assert result[0] == {"title": "CLI Tool", "url": "https://example.com/tool", "source": "hn"}
    assert result[1] == {"title": "Another Tool", "url": "https://news.ycombinator.com/item?id=456", "source": "hn"}
