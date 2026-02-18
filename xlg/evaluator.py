"""Evaluator converts AST to executable pipeline."""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any
from xlg.parser import Pipeline
from xlg.plugins import Registry, load_plugins
from xlg.commands.sources import cmd_read, cmd_fetch
from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum, cmd_github, cmd_wiki
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter, cmd_take, cmd_sort, cmd_summarize
from xlg.commands.sinks import cmd_open, cmd_pause, cmd_play, cmd_previous, cmd_print, cmd_resume, cmd_skip, cmd_status, cmd_store, cmd_toggle, cmd_volume, cmd_write


_plugin_registry: Registry | None = None
_plugin_dir_used: str | None = None


def _get_plugin_registry() -> Registry:
    """Load plugins from config directory and built-in plugins."""
    global _plugin_registry, _plugin_dir_used
    plugin_dir = Path(os.environ.get("XLG_PLUGIN_DIR", Path.home() / ".config" / "xlg" / "plugins"))
    plugin_dir_str = str(plugin_dir)
    if _plugin_registry is None or _plugin_dir_used != plugin_dir_str:
        _plugin_registry = Registry()
        _plugin_dir_used = plugin_dir_str
        from xlg.plugins.fill import register as fill_register
        fill_register(_plugin_registry)
        load_plugins(_plugin_registry, plugin_dir)
    return _plugin_registry


def evaluate(ast: Pipeline, source: Generator | None = None) -> Any:
    """Evaluate a pipeline AST."""
    registry = _get_plugin_registry()
    stream = source
    for cmd in ast.commands:
        name, args = cmd.name, cmd.args
        if name == "read":
            stream = cmd_read(args[0])
        elif name == "fetch":
            stream = cmd_fetch(args[0])
        elif name == "reddit":
            stream = cmd_reddit(args[0], args[1] if len(args) > 1 else "")
        elif name == "hn":
            stream = cmd_hn(args[0])
        elif name == "museum":
            stream = cmd_museum(args[0], args[1])
        elif name == "github":
            stream = cmd_github(args[0])
        elif name == "wiki":
            stream = cmd_wiki(args[0] if args else "")
        elif name == "parse":
            stream = cmd_parse(stream, args[0])
        elif name == "get":
            stream = cmd_get(stream, args[0])
        elif name == "filter":
            stream = cmd_filter(stream, args[0], args[1])
        elif name == "take":
            stream = cmd_take(stream, int(args[0]))
        elif name == "sort":
            stream = cmd_sort(stream, args[0])
        elif name == "summarize":
            stream = cmd_summarize(stream)
        elif name == "print":
            return cmd_print(stream)
        elif name == "write":
            return cmd_write(stream, args[0])
        elif name == "store":
            return cmd_store(stream, args[0])
        elif name == "play":
            return cmd_play(args[0])
        elif name == "pause":
            return cmd_pause()
        elif name == "resume":
            return cmd_resume()
        elif name == "toggle":
            return cmd_toggle()
        elif name == "skip":
            return cmd_skip()
        elif name == "previous":
            return cmd_previous()
        elif name == "volume":
            return cmd_volume(args[0])
        elif name == "status":
            return cmd_status()
        elif name == "open":
            return cmd_open(stream)
        elif name in registry.sources:
            stream = registry.sources[name](*args)
        elif name in registry.transforms:
            stream = registry.transforms[name](stream, *args)
        elif name in registry.sinks:
            return registry.sinks[name](stream, *args)
        else:
            raise ValueError(f"Unknown command: {name}")
    return list(stream) if stream else []
