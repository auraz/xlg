"""Plugin registry tests."""

from xlg.plugins import Registry


def test_registry_add_sink():
    registry = Registry()
    registry.add_sink("test", lambda data, arg: None)
    assert "test" in registry.sinks


def test_registry_add_source():
    registry = Registry()
    registry.add_source("test", lambda arg: iter([]))
    assert "test" in registry.sources


def test_registry_add_transform():
    registry = Registry()
    registry.add_transform("test", lambda stream, arg: stream)
    assert "test" in registry.transforms
