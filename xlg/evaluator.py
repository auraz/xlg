"""Evaluator converts AST to executable pipeline."""
from collections.abc import Generator
from typing import Any
from xlg.parser import Pipeline
from xlg.commands.sources import cmd_read, cmd_fetch
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter, cmd_take, cmd_sort, cmd_summarize
from xlg.commands.sinks import cmd_open, cmd_play, cmd_print, cmd_store, cmd_write


def evaluate(ast: Pipeline, source: Generator | None = None) -> Any:
    """Evaluate a pipeline AST."""
    stream = source
    for cmd in ast.commands:
        name, args = cmd.name, cmd.args
        if name == "read":
            stream = cmd_read(args[0])
        elif name == "fetch":
            stream = cmd_fetch(args[0])
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
        elif name == "open":
            return cmd_open(stream)
        else:
            raise ValueError(f"Unknown command: {name}")
    return list(stream) if stream else []
