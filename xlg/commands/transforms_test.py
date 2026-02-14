"""Transform command tests."""
from xlg.commands.transforms import cmd_parse


def test_parse_json():
    def source():
        yield '{"name": "alice"}'
    result = list(cmd_parse(source(), "json"))
    assert result == [{"name": "alice"}]


def test_parse_csv():
    def source():
        yield "name,age\nalice,30\nbob,25"
    result = list(cmd_parse(source(), "csv"))
    assert result == [{"name": "alice", "age": "30"}, {"name": "bob", "age": "25"}]
