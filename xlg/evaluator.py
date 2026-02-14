"""Evaluator converts AST to executable pipeline."""
from collections.abc import Callable, Generator
from typing import Any
from xlg.parser import Pipeline, Command
from xlg.commands.sources import cmd_read, cmd_fetch
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter, cmd_take, cmd_sort
from xlg.commands.sinks import cmd_print, cmd_store, cmd_write


COMMANDS = {
    "fetch": cmd_fetch,
    "read": cmd_read,
    "parse": cmd_parse,
    "get": cmd_get,
    "filter": cmd_filter,
    "take": cmd_take,
    "sort": cmd_sort,
    "print": cmd_print,
    "write": cmd_write,
    "store": cmd_store,
}


def evaluate(ast: Pipeline, source: Callable[[], Generator] | None = None) -> Any:
    """Evaluate a pipeline AST."""
    stream = source() if source else None
    for cmd in ast.commands:
        handler = COMMANDS.get(cmd.name)
        if handler is None:
            raise ValueError(f"Unknown command: {cmd.name}")
        if cmd.name == "read":
            stream = handler(cmd.args[0])
        elif cmd.name == "fetch":
            stream = handler(cmd.args[0])
        elif cmd.name == "parse":
            stream = handler(stream, cmd.args[0])
        elif cmd.name == "get":
            stream = handler(stream, cmd.args[0])
        elif cmd.name == "filter":
            stream = handler(stream, cmd.args[0], cmd.args[1])
        elif cmd.name == "take":
            stream = handler(stream, int(cmd.args[0]))
        elif cmd.name == "sort":
            stream = handler(stream, cmd.args[0])
        elif cmd.name == "print":
            return handler(stream)
        elif cmd.name == "write":
            return handler(stream, cmd.args[0])
        elif cmd.name == "store":
            return handler(stream, cmd.args[0])
    return list(stream) if stream else []
