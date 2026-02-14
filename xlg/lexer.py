"""Lexer for XLG."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Token types."""

    STRING = auto()
    NUMBER = auto()
    PIPE = auto()
    WORD = auto()


@dataclass
class Token:
    """A lexer token."""

    type: TokenType
    value: str | int | float


def tokenize(source: str) -> list[Token]:
    """Tokenize XLG source code."""
    tokens = []
    i = 0
    while i < len(source):
        c = source[i]
        if c.isspace():
            i += 1
        elif c in ('"', "'"):
            quote = c
            i += 1
            start = i
            while i < len(source) and source[i] != quote:
                i += 1
            tokens.append(Token(TokenType.STRING, source[start:i]))
            i += 1
        elif c == "|":
            tokens.append(Token(TokenType.PIPE, "|"))
            i += 1
        elif c.isdigit():
            start = i
            while i < len(source) and (source[i].isdigit() or source[i] == "."):
                i += 1
            value = source[start:i]
            tokens.append(Token(TokenType.NUMBER, float(value) if "." in value else int(value)))
        elif c.isalpha() or c == "_":
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
            tokens.append(Token(TokenType.WORD, source[start:i]))
        else:
            i += 1
    return tokens
