"""Lexer tests."""
from xlg.lexer import tokenize, Token, TokenType


def test_tokenize_string():
    tokens = tokenize('"hello"')
    assert tokens == [Token(TokenType.STRING, "hello")]


def test_tokenize_number():
    tokens = tokenize("123")
    assert tokens == [Token(TokenType.NUMBER, 123)]


def test_tokenize_float():
    tokens = tokenize("3.14")
    assert tokens == [Token(TokenType.NUMBER, 3.14)]


def test_tokenize_pipe():
    tokens = tokenize("|")
    assert tokens == [Token(TokenType.PIPE, "|")]
