"""Evaluator tests."""
from xlg.evaluator import evaluate
from xlg.parser import Command, Pipeline


def test_evaluate_print(capsys):
    pipeline = Pipeline([Command("print", [])])
    def source():
        yield "hello"
    result = evaluate(pipeline, source)
    assert result == ["hello"]
