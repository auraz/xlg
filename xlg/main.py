"""XLG CLI and REPL."""

import sys
from xlg.lexer import tokenize
from xlg.parser import parse
from xlg.evaluator import evaluate


def run(source: str) -> None:
    """Execute XLG source code."""
    tokens = tokenize(source)
    ast = parse(tokens)
    evaluate(ast)


def repl() -> None:
    """Interactive REPL."""
    print("XLG REPL - type 'exit' to quit")
    while True:
        try:
            line = input("xlg> ")
            if line.strip() == "exit":
                break
            if line.strip():
                run(line)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except Exception as e:
            print(f"Error: {e}")


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "auth":
            from xlg.auth import run_auth_server
            run_auth_server()
        else:
            run(sys.argv[1])
    else:
        repl()


if __name__ == "__main__":
    main()
