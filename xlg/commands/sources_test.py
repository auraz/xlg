"""Source command tests."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from xlg.commands.sources import cmd_read, cmd_fetch


def test_read_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("line1\nline2")
        path = f.name
    result = list(cmd_read(path))
    assert result == ["line1\nline2"]
    Path(path).unlink()


def test_fetch_url():
    mock_response = MagicMock()
    mock_response.text = '{"status": "ok"}'
    with patch("httpx.get", return_value=mock_response):
        result = list(cmd_fetch("https://example.com"))
        assert result == ['{"status": "ok"}']
