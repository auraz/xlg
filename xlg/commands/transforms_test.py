"""Transform command tests."""
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter


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


def test_get_nested():
    def source():
        yield {"data": {"items": [1, 2, 3]}}
    result = list(cmd_get(source(), "data.items"))
    assert result == [[1, 2, 3]]


def test_filter_by_field():
    def source():
        yield {"name": "alice", "active": "true"}
        yield {"name": "bob", "active": "false"}
    result = list(cmd_filter(source(), "active", "true"))
    assert result == [{"name": "alice", "active": "true"}]
