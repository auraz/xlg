"""Sink command tests."""
import sqlite3
import tempfile
from pathlib import Path
from xlg.commands.sinks import cmd_print, cmd_store, cmd_write


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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        path = f.name
    result = cmd_write(source(), path)
    assert result == 1
    assert Path(path).read_text() == "hello world"
    Path(path).unlink()


def test_store_sqlite():
    def source():
        yield {"name": "alice", "age": 30}
        yield {"name": "bob", "age": 25}
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        path = f.name
    result = cmd_store(source(), path)
    assert result == 2
    conn = sqlite3.connect(path)
    rows = conn.execute("SELECT * FROM data").fetchall()
    assert len(rows) == 2
    conn.close()
    Path(path).unlink()
