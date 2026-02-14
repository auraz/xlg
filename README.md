# XLG - eXpression LanGuage

Express complex operations in single commands.

```
fetch "api.example.com/users" | parse json | store "users.db"
```

## Status

In development. See [design doc](docs/plans/2026-02-14-xlg-design.md).

## Components

- **Lexer**: Tokenizes XLG source into tokens (STRING, NUMBER, PIPE, WORD) - complete
- **Parser**: Builds AST (Pipeline of Commands) from tokens - complete
- **Pipeline**: Chains generators together for lazy evaluation - complete
- **Commands**: Built-in commands (read source, print sink, parse transform) - in progress
- **Evaluator**: Executes pipeline AST by wiring commands together - complete
- **CLI/REPL**: Command-line interface and interactive REPL - complete
