"""Evaluator converts AST to executable pipeline."""
from collections.abc import Callable, Generator
from typing import Any
from xlg.parser import Pipeline, Command
from xlg.commands.sources import cmd_read, cmd_fetch
from xlg.commands.transforms import cmd_parse
from xlg.commands.sinks import cmd_print


COMMANDS = {
    "fetch": cmd_fetch,
    "read": cmd_read,
    "parse": cmd_parse,
    "print": cmd_print,
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
        elif cmd.name == "print":
            return handler(stream)
    return list(stream) if stream else []
