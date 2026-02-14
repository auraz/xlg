"""Lexer tests."""
from xlg.lexer import tokenize, Token, TokenType


def test_tokenize_string():
    tokens = tokenize('"hello"')
    assert tokens == [Token(TokenType.STRING, "hello")]
