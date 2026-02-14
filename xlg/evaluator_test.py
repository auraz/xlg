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
    result = evaluate(pipeline, source)
    assert result == ["hello"]


def test_read_parse_print(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"name": "alice"}')
        path = f.name
    source = f'read "{path}" | parse json | print'
    tokens = tokenize(source)
    ast = parse(tokens)
    result = evaluate(ast)
    assert result == [{"name": "alice"}]
    Path(path).unlink()
