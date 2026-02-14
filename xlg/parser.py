"""Parser for XLG."""
from dataclasses import dataclass
from xlg.lexer import Token, TokenType


@dataclass
class Command:
    """A command with arguments."""
    name: str
    args: list[str | int | float]


@dataclass
class Pipeline:
    """A pipeline of commands."""
    commands: list[Command]


def parse(tokens: list[Token]) -> Pipeline:
    """Parse tokens into AST."""
    commands = []
    i = 0
    while i < len(tokens):
        if tokens[i].type == TokenType.WORD:
            name = tokens[i].value
            args = []
            i += 1
            while i < len(tokens) and tokens[i].type != TokenType.PIPE:
                args.append(tokens[i].value)
                i += 1
            commands.append(Command(name, args))
            if i < len(tokens) and tokens[i].type == TokenType.PIPE:
                i += 1
        else:
            i += 1
    return Pipeline(commands)
