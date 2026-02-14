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


def test_tokenize_word():
    tokens = tokenize("fetch")
    assert tokens == [Token(TokenType.WORD, "fetch")]


def test_tokenize_pipeline():
    tokens = tokenize('fetch "url" | parse json')
    assert tokens == [
        Token(TokenType.WORD, "fetch"),
        Token(TokenType.STRING, "url"),
        Token(TokenType.PIPE, "|"),
        Token(TokenType.WORD, "parse"),
        Token(TokenType.WORD, "json"),
    ]
