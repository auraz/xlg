"""Parser tests."""

from xlg.parser import parse, Command, Pipeline
from xlg.lexer import tokenize


def test_parse_single_command():
    tokens = tokenize('print "hello"')
    ast = parse(tokens)
    assert ast == Pipeline([Command("print", ["hello"])])


def test_parse_pipeline():
    tokens = tokenize('fetch "url" | parse json | print')
    ast = parse(tokens)
    assert ast == Pipeline([Command("fetch", ["url"]), Command("parse", ["json"]), Command("print", [])])
