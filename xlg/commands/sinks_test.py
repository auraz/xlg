"""Sink command tests."""
import tempfile
from pathlib import Path
from xlg.commands.sinks import cmd_print, cmd_write


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
