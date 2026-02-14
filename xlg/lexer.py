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
        if source[i] == '"':
            i += 1
            start = i
            while i < len(source) and source[i] != '"':
                i += 1
            tokens.append(Token(TokenType.STRING, source[start:i]))
            i += 1
        else:
            i += 1
    return tokens
