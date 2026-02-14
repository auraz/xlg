"""End-to-end integration tests."""
import tempfile
from pathlib import Path
from xlg.lexer import tokenize
from xlg.parser import parse
from xlg.evaluator import evaluate


def run(source: str):
    """Run XLG source code and return result."""
    return evaluate(parse(tokenize(source)))


def test_read_parse_filter_print(capsys):
    """Test CSV read, parse, filter and print pipeline."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,active\nalice,true\nbob,false\ncharlie,true")
        path = f.name
    result = run(f'read "{path}" | parse csv | filter "active" "true" | print')
    assert len(result) == 2
    assert result[0]["name"] == "alice"
    Path(path).unlink()


def test_full_pipeline():
    """Test JSON read, parse, get and store pipeline."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"data": [{"name": "a"}, {"name": "b"}, {"name": "c"}]}')
        json_path = f.name
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    result = run(f'read "{json_path}" | parse json | get "data" | store "{db_path}"')
    assert result == 3
    Path(json_path).unlink()
    Path(db_path).unlink()


def test_discovery_pipeline_structure():
    """Test discovery pipeline yields correct structure."""
    from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum
    assert callable(cmd_reddit)
    assert callable(cmd_hn)
    assert callable(cmd_museum)
