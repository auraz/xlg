"""Plugin registry tests."""

from xlg.plugins import Registry, load_plugins


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


def test_load_plugins_from_directory(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "test_plugin.py"
    plugin_file.write_text('def register(registry):\n    registry.add_sink("test_cmd", lambda data, arg: "ok")\n')
    registry = Registry()
    load_plugins(registry, plugin_dir)
    assert "test_cmd" in registry.sinks


def test_load_plugins_handles_missing_dir(tmp_path):
    registry = Registry()
    load_plugins(registry, tmp_path / "nonexistent")
    assert len(registry.sinks) == 0
