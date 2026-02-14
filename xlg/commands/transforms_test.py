"""Transform command tests."""
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter, cmd_take, cmd_sort


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
    """Test get with nested path, flattening list results."""
    def source():
        yield {"data": {"items": [1, 2, 3]}}
    result = list(cmd_get(source(), "data.items"))
    assert result == [1, 2, 3]


def test_filter_by_field():
    def source():
        yield {"name": "alice", "active": "true"}
        yield {"name": "bob", "active": "false"}
    result = list(cmd_filter(source(), "active", "true"))
    assert result == [{"name": "alice", "active": "true"}]


def test_take_n():
    def source():
        yield 1
        yield 2
        yield 3
        yield 4
    result = list(cmd_take(source(), 2))
    assert result == [1, 2]


def test_sort_by_field():
    def source():
        yield {"name": "charlie", "age": 35}
        yield {"name": "alice", "age": 25}
        yield {"name": "bob", "age": 30}
    result = list(cmd_sort(source(), "name"))
    assert result[0]["name"] == "alice"
    assert result[1]["name"] == "bob"
    assert result[2]["name"] == "charlie"


def test_cmd_parse_rss():
    """Test parse rss yields items with title, url, source."""
    rss_content = '''<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item><title>Post 1</title><link>https://example.com/1</link></item>
            <item><title>Post 2</title><link>https://example.com/2</link></item>
        </channel>
    </rss>'''
    result = list(cmd_parse(iter([rss_content]), "rss"))
    assert len(result) == 2
    assert result[0] == {"title": "Post 1", "url": "https://example.com/1", "source": "rss"}
