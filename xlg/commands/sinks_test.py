"""Sink command tests."""

import sqlite3
import tempfile
from pathlib import Path
from xlg.commands.sinks import cmd_open, cmd_print, cmd_store, cmd_write


def test_print_collects_output(capsys):
    def source():
        yield "hello"
        yield "world"

    result = cmd_print(source())
    assert result == ["hello", "world"]
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "world" in captured.out


def test_write_file():
    def source():
        yield "hello world"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        path = f.name
    result = cmd_write(source(), path)
    assert result == 1
    assert Path(path).read_text() == "hello world"
    Path(path).unlink()


def test_store_sqlite():
    def source():
        yield {"name": "alice", "age": 30}
        yield {"name": "bob", "age": 25}

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    result = cmd_store(source(), path)
    assert result == 2
    conn = sqlite3.connect(path)
    rows = conn.execute("SELECT * FROM data").fetchall()
    assert len(rows) == 2
    conn.close()
    Path(path).unlink()


def test_cmd_open(mocker):
    """Test open command opens URLs in browser."""
    mock_run = mocker.patch("subprocess.run")
    items = iter([{"title": "Art", "url": "https://example.com/art"}, {"title": "Music", "url": "https://example.com/music"}])
    result = cmd_open(items)
    assert result == ["https://example.com/art", "https://example.com/music"]
    assert mock_run.call_count == 2


def test_cmd_play_musickit_uses_socket_when_running(mocker):
    """Test play sends to existing player via socket."""
    mocker.patch('xlg.config.load_config', return_value={
        'APPLE_MUSIC_KEY_ID': 'test-key-id',
        'APPLE_MUSIC_TEAM_ID': 'test-team-id',
        'APPLE_MUSIC_KEY_PATH': '',
    })
    mocker.patch.dict('os.environ', {
        'APPLE_MUSIC_KEY_ID': 'test-key-id',
        'APPLE_MUSIC_TEAM_ID': 'test-team-id',
        'APPLE_MUSIC_PRIVATE_KEY': 'test-private-key',
    })
    mock_am = mocker.MagicMock()
    mock_am.search.return_value = {'results': {'songs': {'data': [{'id': '123456789', 'attributes': {'name': 'Test Song'}}]}}}
    mocker.patch('xlg.commands.sinks.AppleMusic', return_value=mock_am)
    mocker.patch('pathlib.Path.exists', return_value=True)
    mock_send = mocker.patch('xlg.commands.sinks.send_to_player', return_value=True)

    from xlg.commands.sinks import cmd_play
    result = cmd_play("Gorillaz")

    mock_send.assert_called_once_with('123456789')
    assert result == 'Playing: Test Song'


def test_cmd_play_musickit_starts_new_player(mocker):
    """Test play starts new player when socket fails."""
    mocker.patch('xlg.config.load_config', return_value={
        'APPLE_MUSIC_KEY_ID': 'test-key-id',
        'APPLE_MUSIC_TEAM_ID': 'test-team-id',
        'APPLE_MUSIC_KEY_PATH': '',
    })
    mocker.patch.dict('os.environ', {
        'APPLE_MUSIC_KEY_ID': 'test-key-id',
        'APPLE_MUSIC_TEAM_ID': 'test-team-id',
        'APPLE_MUSIC_PRIVATE_KEY': 'test-private-key',
    })
    mock_am = mocker.MagicMock()
    mock_am.search.return_value = {'results': {'songs': {'data': [{'id': '123456789', 'attributes': {'name': 'Test Song'}}]}}}
    mocker.patch('xlg.commands.sinks.AppleMusic', return_value=mock_am)
    mocker.patch('pathlib.Path.exists', return_value=True)
    mocker.patch('xlg.commands.sinks.send_to_player', return_value=False)
    mock_popen = mocker.patch('subprocess.Popen')

    from xlg.commands.sinks import cmd_play
    result = cmd_play("Gorillaz")

    mock_popen.assert_called_once()
    assert '123456789' in mock_popen.call_args[0][0][1]
    assert result == 'Playing: Test Song'


def test_cmd_play_falls_back_to_applescript(mocker):
    """Test play falls back to AppleScript when MusicKit not configured."""
    mocker.patch('xlg.config.load_config', return_value={})
    mocker.patch.dict('os.environ', {}, clear=True)

    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "playing:Test Song"
    mock_run.return_value.stderr = ""

    from xlg.commands.sinks import cmd_play
    result = cmd_play("Beatles")

    assert mock_run.call_args_list[0][0][0][0] == "osascript"
    assert "Playing: Test Song" in result
