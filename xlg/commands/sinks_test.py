"""Sink command tests."""
from xlg.commands.sinks import cmd_print


def test_print_collects_output(capsys):
    def source():
        yield "hello"
        yield "world"
    result = cmd_print(source())
    assert result == ["hello", "world"]
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "world" in captured.out
