"""Evaluator tests."""

import tempfile
from pathlib import Path
from xlg.evaluator import evaluate
from xlg.lexer import tokenize
from xlg.parser import Command, Pipeline, parse


def test_evaluate_print(capsys):
    pipeline = Pipeline([Command("print", [])])

    def source():
        yield "hello"

    result = evaluate(pipeline, source())
    assert result == ["hello"]


def test_read_parse_print(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"name": "alice"}')
        path = f.name
    source = f'read "{path}" | parse json | print'
    tokens = tokenize(source)
    ast = parse(tokens)
    result = evaluate(ast)
    assert result == [{"name": "alice"}]
    Path(path).unlink()


def test_evaluate_plugin_sink(tmp_path, monkeypatch):
    """Test that plugins are loaded and usable in evaluator."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "echo.py"
    plugin_file.write_text("""
def register(registry):
    registry.add_sink("echo", lambda data, msg: f"echoed: {msg}")
""")
    monkeypatch.setenv("XLG_PLUGIN_DIR", str(plugin_dir))
    tokens = tokenize('echo "hello"')
    ast = parse(tokens)
    result = evaluate(ast)
    assert result == "echoed: hello"
