# XLG Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build XLG interpreter - a shell-like language for expressing complex operations in single pipeable commands.

**Architecture:** Pipeline-first with Python generators. Lexer tokenizes input, parser builds AST, evaluator creates pipeline of chained generators, sink commands consume and terminate.

**Tech Stack:** Python 3.12+, uv, pytest, ruff, httpx, sqlite3

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `justfile`
- Create: `xlg/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "xlg"
version = "0.1.0"
description = "eXpression LanGuage - express complex operations in single commands"
requires-python = ">=3.12"
dependencies = ["httpx>=0.27"]

[project.scripts]
xlg = "xlg.main:main"

[tool.ruff]
line-length = 170

[tool.pytest.ini_options]
testpaths = ["xlg"]
python_files = ["*_test.py"]
```

**Step 2: Create justfile**

```just
default:
    @just --list

test:
    uv run pytest -v

lint:
    uv run ruff check xlg

fmt:
    uv run ruff format xlg

run *ARGS:
    uv run xlg {{ARGS}}
```

**Step 3: Create xlg/__init__.py**

```python
"""XLG - eXpression LanGuage."""
```

**Step 4: Initialize uv and install deps**

Run: `uv sync`
Expected: Creates .venv and installs dependencies

**Step 5: Commit**

```bash
git add pyproject.toml justfile xlg/__init__.py
git commit -m "feat: project setup with uv"
```

---

## Task 2: Lexer - Token Types

**Files:**
- Create: `xlg/lexer.py`
- Create: `xlg/lexer_test.py`

**Step 1: Write failing test for tokenizing string**

```python
"""Lexer tests."""
from xlg.lexer import tokenize, Token, TokenType


def test_tokenize_string():
    tokens = tokenize('"hello"')
    assert tokens == [Token(TokenType.STRING, "hello")]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL with "cannot import name 'tokenize'"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/lexer.py xlg/lexer_test.py
git commit -m "feat: lexer tokenizes strings"
```

---

## Task 3: Lexer - Numbers and Pipes

**Files:**
- Modify: `xlg/lexer.py`
- Modify: `xlg/lexer_test.py`

**Step 1: Write failing tests**

Add to `xlg/lexer_test.py`:

```python
def test_tokenize_number():
    tokens = tokenize("123")
    assert tokens == [Token(TokenType.NUMBER, 123)]


def test_tokenize_float():
    tokens = tokenize("3.14")
    assert tokens == [Token(TokenType.NUMBER, 3.14)]


def test_tokenize_pipe():
    tokens = tokenize("|")
    assert tokens == [Token(TokenType.PIPE, "|")]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Update tokenize function**

Replace tokenize function in `xlg/lexer.py`:

```python
def tokenize(source: str) -> list[Token]:
    """Tokenize XLG source code."""
    tokens = []
    i = 0
    while i < len(source):
        c = source[i]
        if c.isspace():
            i += 1
        elif c == '"':
            i += 1
            start = i
            while i < len(source) and source[i] != '"':
                i += 1
            tokens.append(Token(TokenType.STRING, source[start:i]))
            i += 1
        elif c == '|':
            tokens.append(Token(TokenType.PIPE, "|"))
            i += 1
        elif c.isdigit():
            start = i
            while i < len(source) and (source[i].isdigit() or source[i] == '.'):
                i += 1
            value = source[start:i]
            tokens.append(Token(TokenType.NUMBER, float(value) if '.' in value else int(value)))
        else:
            i += 1
    return tokens
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/lexer.py xlg/lexer_test.py
git commit -m "feat: lexer tokenizes numbers and pipes"
```

---

## Task 4: Lexer - Words (Command Names)

**Files:**
- Modify: `xlg/lexer.py`
- Modify: `xlg/lexer_test.py`

**Step 1: Write failing test**

Add to `xlg/lexer_test.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add word tokenization**

Add else branch before final else in tokenize:

```python
        elif c.isalpha() or c == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            tokens.append(Token(TokenType.WORD, source[start:i]))
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/lexer.py xlg/lexer_test.py
git commit -m "feat: lexer tokenizes words"
```

---

## Task 5: Parser - AST Types

**Files:**
- Create: `xlg/parser.py`
- Create: `xlg/parser_test.py`

**Step 1: Write failing test**

```python
"""Parser tests."""
from xlg.parser import parse, Command, Pipeline
from xlg.lexer import tokenize


def test_parse_single_command():
    tokens = tokenize('print "hello"')
    ast = parse(tokens)
    assert ast == Pipeline([Command("print", ["hello"])])
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL with "cannot import name 'parse'"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/parser.py xlg/parser_test.py
git commit -m "feat: parser builds AST from tokens"
```

---

## Task 6: Parser - Multi-Command Pipeline

**Files:**
- Modify: `xlg/parser_test.py`

**Step 1: Write test for pipeline**

Add to `xlg/parser_test.py`:

```python
def test_parse_pipeline():
    tokens = tokenize('fetch "url" | parse json | print')
    ast = parse(tokens)
    assert ast == Pipeline([
        Command("fetch", ["url"]),
        Command("parse", ["json"]),
        Command("print", []),
    ])
```

**Step 2: Run test to verify it passes**

Run: `just test`
Expected: PASS (existing implementation handles this)

**Step 3: Commit**

```bash
git add xlg/parser_test.py
git commit -m "test: verify pipeline parsing"
```

---

## Task 7: Pipeline Engine

**Files:**
- Create: `xlg/pipeline.py`
- Create: `xlg/pipeline_test.py`

**Step 1: Write failing test**

```python
"""Pipeline engine tests."""
from xlg.pipeline import run_pipeline


def test_run_pipeline_single():
    def source():
        yield "hello"
    result = list(run_pipeline([source]))
    assert result == ["hello"]


def test_run_pipeline_chain():
    def source():
        yield 1
        yield 2
    def double(upstream):
        for item in upstream:
            yield item * 2
    result = list(run_pipeline([source, double]))
    assert result == [2, 4]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL with "cannot import name 'run_pipeline'"

**Step 3: Write minimal implementation**

```python
"""Pipeline execution engine."""
from collections.abc import Callable, Generator
from typing import Any

Source = Callable[[], Generator[Any, None, None]]
Transform = Callable[[Generator[Any, None, None]], Generator[Any, None, None]]
Stage = Source | Transform


def run_pipeline(stages: list[Stage]) -> Generator[Any, None, None]:
    """Chain and execute pipeline stages."""
    if not stages:
        return
    stream = stages[0]()
    for stage in stages[1:]:
        stream = stage(stream)
    yield from stream
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/pipeline.py xlg/pipeline_test.py
git commit -m "feat: pipeline engine chains generators"
```

---

## Task 8: Print Command

**Files:**
- Create: `xlg/commands/__init__.py`
- Create: `xlg/commands/sinks.py`
- Create: `xlg/commands/sinks_test.py`

**Step 1: Write failing test**

```python
"""Sink command tests."""
from xlg.commands.sinks import cmd_print


def test_print_collects_output(capsys):
    def source():
        yield "hello"
        yield "world"
    result = cmd_print(source())
    assert result == ["hello", "world"]
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "world" in captured.out
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Create commands package and print command**

`xlg/commands/__init__.py`:
```python
"""XLG built-in commands."""
```

`xlg/commands/sinks.py`:
```python
"""Sink commands that consume pipelines."""
from collections.abc import Generator
from typing import Any


def cmd_print(upstream: Generator[Any, None, None]) -> list[Any]:
    """Print each item and return collected results."""
    results = []
    for item in upstream:
        print(item)
        results.append(item)
    return results
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/__init__.py xlg/commands/sinks.py xlg/commands/sinks_test.py
git commit -m "feat: print sink command"
```

---

## Task 9: Read Source Command

**Files:**
- Create: `xlg/commands/sources.py`
- Create: `xlg/commands/sources_test.py`

**Step 1: Write failing test**

```python
"""Source command tests."""
import tempfile
from pathlib import Path
from xlg.commands.sources import cmd_read


def test_read_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("line1\nline2")
        path = f.name
    result = list(cmd_read(path))
    assert result == ["line1\nline2"]
    Path(path).unlink()
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Write implementation**

```python
"""Source commands that start pipelines."""
from collections.abc import Generator
from pathlib import Path


def cmd_read(path: str) -> Generator[str, None, None]:
    """Read file content."""
    yield Path(path).read_text()
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/sources.py xlg/commands/sources_test.py
git commit -m "feat: read source command"
```

---

## Task 10: Parse Transform Command

**Files:**
- Create: `xlg/commands/transforms.py`
- Create: `xlg/commands/transforms_test.py`

**Step 1: Write failing test**

```python
"""Transform command tests."""
from xlg.commands.transforms import cmd_parse


def test_parse_json():
    def source():
        yield '{"name": "alice"}'
    result = list(cmd_parse(source(), "json"))
    assert result == [{"name": "alice"}]


def test_parse_csv():
    def source():
        yield "name,age\nalice,30\nbob,25"
    result = list(cmd_parse(source(), "csv"))
    assert result == [{"name": "alice", "age": "30"}, {"name": "bob", "age": "25"}]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Write implementation**

```python
"""Transform commands for pipelines."""
import csv
import json
from collections.abc import Generator
from io import StringIO
from typing import Any


def cmd_parse(upstream: Generator[Any, None, None], format: str) -> Generator[Any, None, None]:
    """Parse input data according to format."""
    for item in upstream:
        if format == "json":
            yield json.loads(item)
        elif format == "csv":
            reader = csv.DictReader(StringIO(item))
            yield from reader
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/transforms.py xlg/commands/transforms_test.py
git commit -m "feat: parse transform for json and csv"
```

---

## Task 11: Evaluator

**Files:**
- Create: `xlg/evaluator.py`
- Create: `xlg/evaluator_test.py`

**Step 1: Write failing test**

```python
"""Evaluator tests."""
from xlg.evaluator import evaluate
from xlg.parser import Command, Pipeline


def test_evaluate_print(capsys):
    pipeline = Pipeline([Command("print", [])])
    def source():
        yield "hello"
    result = evaluate(pipeline, source)
    assert result == ["hello"]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Write implementation**

```python
"""Evaluator converts AST to executable pipeline."""
from collections.abc import Callable, Generator
from typing import Any
from xlg.parser import Pipeline, Command
from xlg.commands.sources import cmd_read
from xlg.commands.transforms import cmd_parse
from xlg.commands.sinks import cmd_print


COMMANDS = {
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
        elif cmd.name == "parse":
            stream = handler(stream, cmd.args[0])
        elif cmd.name == "print":
            return handler(stream)
    return list(stream) if stream else []
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/evaluator.py xlg/evaluator_test.py
git commit -m "feat: evaluator executes pipeline AST"
```

---

## Task 12: End-to-End Integration

**Files:**
- Modify: `xlg/evaluator_test.py`

**Step 1: Write integration test**

Add to `xlg/evaluator_test.py`:

```python
import tempfile
from pathlib import Path
from xlg.lexer import tokenize
from xlg.parser import parse


def test_read_parse_print(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"name": "alice"}')
        path = f.name
    source = f'read "{path}" | parse json | print'
    tokens = tokenize(source)
    ast = parse(tokens)
    result = evaluate(ast)
    assert result == [{"name": "alice"}]
    Path(path).unlink()
```

**Step 2: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 3: Commit**

```bash
git add xlg/evaluator_test.py
git commit -m "test: end-to-end read | parse | print"
```

---

## Task 13: REPL and CLI

**Files:**
- Create: `xlg/main.py`

**Step 1: Write CLI entry point**

```python
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
        run(sys.argv[1])
    else:
        repl()


if __name__ == "__main__":
    main()
```

**Step 2: Test REPL manually**

Run: `just run`
Expected: Shows "XLG REPL" prompt

**Step 3: Commit**

```bash
git add xlg/main.py
git commit -m "feat: CLI and REPL"
```

---

## Task 14: Fetch Command

**Files:**
- Modify: `xlg/commands/sources.py`
- Modify: `xlg/commands/sources_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write failing test**

Add to `xlg/commands/sources_test.py`:

```python
from xlg.commands.sources import cmd_fetch
from unittest.mock import patch, MagicMock


def test_fetch_url():
    mock_response = MagicMock()
    mock_response.text = '{"status": "ok"}'
    with patch('httpx.get', return_value=mock_response):
        result = list(cmd_fetch("https://example.com"))
        assert result == ['{"status": "ok"}']
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add fetch implementation**

Add to `xlg/commands/sources.py`:

```python
import httpx


def cmd_fetch(url: str) -> Generator[str, None, None]:
    """Fetch URL content."""
    response = httpx.get(url)
    response.raise_for_status()
    yield response.text
```

**Step 4: Add fetch to evaluator**

Add to COMMANDS dict in `xlg/evaluator.py`:
```python
from xlg.commands.sources import cmd_read, cmd_fetch

COMMANDS = {
    "fetch": cmd_fetch,
    "read": cmd_read,
    ...
}
```

And add handler in evaluate:
```python
        elif cmd.name == "fetch":
            stream = handler(cmd.args[0])
```

**Step 5: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 6: Commit**

```bash
git add xlg/commands/sources.py xlg/commands/sources_test.py xlg/evaluator.py
git commit -m "feat: fetch command for HTTP GET"
```

---

## Task 15: Write Sink Command

**Files:**
- Modify: `xlg/commands/sinks.py`
- Modify: `xlg/commands/sinks_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write failing test**

Add to `xlg/commands/sinks_test.py`:

```python
import tempfile
from pathlib import Path
from xlg.commands.sinks import cmd_write


def test_write_file():
    def source():
        yield "hello world"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        path = f.name
    result = cmd_write(source(), path)
    assert result == 1
    assert Path(path).read_text() == "hello world"
    Path(path).unlink()
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add write implementation**

Add to `xlg/commands/sinks.py`:

```python
from pathlib import Path


def cmd_write(upstream: Generator[Any, None, None], path: str) -> int:
    """Write items to file."""
    count = 0
    with open(path, 'w') as f:
        for item in upstream:
            f.write(str(item))
            count += 1
    return count
```

**Step 4: Add write to evaluator**

Add to COMMANDS and evaluate handler.

**Step 5: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 6: Commit**

```bash
git add xlg/commands/sinks.py xlg/commands/sinks_test.py xlg/evaluator.py
git commit -m "feat: write sink command"
```

---

## Task 16: Store SQLite Command

**Files:**
- Modify: `xlg/commands/sinks.py`
- Modify: `xlg/commands/sinks_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write failing test**

Add to `xlg/commands/sinks_test.py`:

```python
import sqlite3
from xlg.commands.sinks import cmd_store


def test_store_sqlite():
    def source():
        yield {"name": "alice", "age": 30}
        yield {"name": "bob", "age": 25}
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        path = f.name
    result = cmd_store(source(), path)
    assert result == 2
    conn = sqlite3.connect(path)
    rows = conn.execute("SELECT * FROM data").fetchall()
    assert len(rows) == 2
    conn.close()
    Path(path).unlink()
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add store implementation**

Add to `xlg/commands/sinks.py`:

```python
import sqlite3


def cmd_store(upstream: Generator[Any, None, None], path: str) -> int:
    """Store items in SQLite database."""
    conn = sqlite3.connect(path)
    count = 0
    for item in upstream:
        if isinstance(item, dict):
            if count == 0:
                cols = ", ".join(item.keys())
                placeholders = ", ".join("?" * len(item))
                conn.execute(f"CREATE TABLE IF NOT EXISTS data ({cols})")
            conn.execute(f"INSERT INTO data VALUES ({placeholders})", list(item.values()))
            count += 1
    conn.commit()
    conn.close()
    return count
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/sinks.py xlg/commands/sinks_test.py xlg/evaluator.py
git commit -m "feat: store command for SQLite"
```

---

## Task 17: Get Transform Command

**Files:**
- Modify: `xlg/commands/transforms.py`
- Modify: `xlg/commands/transforms_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write failing test**

Add to `xlg/commands/transforms_test.py`:

```python
from xlg.commands.transforms import cmd_get


def test_get_nested():
    def source():
        yield {"data": {"items": [1, 2, 3]}}
    result = list(cmd_get(source(), "data.items"))
    assert result == [[1, 2, 3]]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add get implementation**

Add to `xlg/commands/transforms.py`:

```python
def cmd_get(upstream: Generator[Any, None, None], path: str) -> Generator[Any, None, None]:
    """Extract nested field by dot-path."""
    for item in upstream:
        value = item
        for key in path.split('.'):
            value = value[key]
        yield value
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/transforms.py xlg/commands/transforms_test.py xlg/evaluator.py
git commit -m "feat: get transform for nested field access"
```

---

## Task 18: Filter Transform Command

**Files:**
- Modify: `xlg/commands/transforms.py`
- Modify: `xlg/commands/transforms_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write failing test**

Add to `xlg/commands/transforms_test.py`:

```python
from xlg.commands.transforms import cmd_filter


def test_filter_by_field():
    def source():
        yield {"name": "alice", "active": "true"}
        yield {"name": "bob", "active": "false"}
    result = list(cmd_filter(source(), "active", "true"))
    assert result == [{"name": "alice", "active": "true"}]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add filter implementation**

Add to `xlg/commands/transforms.py`:

```python
def cmd_filter(upstream: Generator[Any, None, None], field: str, value: str) -> Generator[Any, None, None]:
    """Filter items where field equals value."""
    for item in upstream:
        if str(item.get(field)) == str(value):
            yield item
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/transforms.py xlg/commands/transforms_test.py xlg/evaluator.py
git commit -m "feat: filter transform command"
```

---

## Task 19: Take Transform Command

**Files:**
- Modify: `xlg/commands/transforms.py`
- Modify: `xlg/commands/transforms_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write failing test**

Add to `xlg/commands/transforms_test.py`:

```python
from xlg.commands.transforms import cmd_take


def test_take_n():
    def source():
        yield 1
        yield 2
        yield 3
        yield 4
    result = list(cmd_take(source(), 2))
    assert result == [1, 2]
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add take implementation**

Add to `xlg/commands/transforms.py`:

```python
def cmd_take(upstream: Generator[Any, None, None], n: int) -> Generator[Any, None, None]:
    """Take first n items."""
    count = 0
    for item in upstream:
        if count >= n:
            break
        yield item
        count += 1
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/transforms.py xlg/commands/transforms_test.py xlg/evaluator.py
git commit -m "feat: take transform command"
```

---

## Task 20: Sort Transform Command

**Files:**
- Modify: `xlg/commands/transforms.py`
- Modify: `xlg/commands/transforms_test.py`
- Modify: `xlg/evaluator.py`

**Step 1: Write failing test**

Add to `xlg/commands/transforms_test.py`:

```python
from xlg.commands.transforms import cmd_sort


def test_sort_by_field():
    def source():
        yield {"name": "charlie", "age": 35}
        yield {"name": "alice", "age": 25}
        yield {"name": "bob", "age": 30}
    result = list(cmd_sort(source(), "name"))
    assert result[0]["name"] == "alice"
    assert result[1]["name"] == "bob"
    assert result[2]["name"] == "charlie"
```

**Step 2: Run test to verify it fails**

Run: `just test`
Expected: FAIL

**Step 3: Add sort implementation**

Add to `xlg/commands/transforms.py`:

```python
def cmd_sort(upstream: Generator[Any, None, None], field: str) -> Generator[Any, None, None]:
    """Sort items by field."""
    items = list(upstream)
    items.sort(key=lambda x: x.get(field, ""))
    yield from items
```

**Step 4: Run test to verify it passes**

Run: `just test`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/commands/transforms.py xlg/commands/transforms_test.py xlg/evaluator.py
git commit -m "feat: sort transform command"
```

---

## Task 21: Complete Evaluator

**Files:**
- Modify: `xlg/evaluator.py`

**Step 1: Refactor evaluator to handle all commands**

Replace `xlg/evaluator.py`:

```python
"""Evaluator converts AST to executable pipeline."""
from collections.abc import Generator
from typing import Any
from xlg.parser import Pipeline
from xlg.commands.sources import cmd_read, cmd_fetch
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter, cmd_take, cmd_sort
from xlg.commands.sinks import cmd_print, cmd_write, cmd_store


def evaluate(ast: Pipeline, source: Generator | None = None) -> Any:
    """Evaluate a pipeline AST."""
    stream = source
    for cmd in ast.commands:
        name, args = cmd.name, cmd.args
        if name == "read":
            stream = cmd_read(args[0])
        elif name == "fetch":
            stream = cmd_fetch(args[0])
        elif name == "parse":
            stream = cmd_parse(stream, args[0])
        elif name == "get":
            stream = cmd_get(stream, args[0])
        elif name == "filter":
            stream = cmd_filter(stream, args[0], args[1])
        elif name == "take":
            stream = cmd_take(stream, int(args[0]))
        elif name == "sort":
            stream = cmd_sort(stream, args[0])
        elif name == "print":
            return cmd_print(stream)
        elif name == "write":
            return cmd_write(stream, args[0])
        elif name == "store":
            return cmd_store(stream, args[0])
        else:
            raise ValueError(f"Unknown command: {name}")
    return list(stream) if stream else []
```

**Step 2: Run all tests**

Run: `just test`
Expected: All PASS

**Step 3: Commit**

```bash
git add xlg/evaluator.py
git commit -m "refactor: complete evaluator with all commands"
```

---

## Task 22: Demo Site

**Files:**
- Create: `site/index.html`

**Step 1: Create demo page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XLG - eXpression LanGuage</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #0a0a0f; color: #e0e0e0; line-height: 1.6; }
        .hero { text-align: center; padding: 80px 20px; background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0f 100%); }
        h1 { font-size: 3.5rem; margin-bottom: 10px; background: linear-gradient(90deg, #00d4ff, #7b2fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tagline { font-size: 1.5rem; color: #888; margin-bottom: 40px; }
        pre { background: #12121a; border-radius: 8px; padding: 20px; overflow-x: auto; text-align: left; margin: 20px auto; max-width: 700px; border: 1px solid #2a2a3a; }
        code { color: #00d4ff; font-family: 'SF Mono', Monaco, monospace; font-size: 1.1rem; }
        .section { padding: 60px 20px; max-width: 900px; margin: 0 auto; }
        h2 { font-size: 2rem; margin-bottom: 30px; color: #fff; }
        .example { margin-bottom: 40px; }
        .example h3 { color: #7b2fff; margin-bottom: 10px; font-size: 1.2rem; }
        .comparison { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        .comparison pre { margin: 0; }
        .label { font-size: 0.8rem; color: #666; margin-bottom: 5px; text-transform: uppercase; }
        .install { background: #12121a; padding: 40px; border-radius: 12px; text-align: center; }
        .install code { background: #1a1a2e; padding: 15px 30px; border-radius: 6px; display: inline-block; }
        .cmd { color: #7b2fff; }
        .str { color: #98c379; }
        .comment { color: #666; }
    </style>
</head>
<body>
    <div class="hero">
        <h1>XLG</h1>
        <p class="tagline">Express more in one line</p>
        <pre><code><span class="cmd">fetch</span> <span class="str">"api.example.com/users"</span> | <span class="cmd">parse</span> json | <span class="cmd">store</span> <span class="str">"users.db"</span></code></pre>
    </div>

    <div class="section">
        <h2>Use Cases</h2>

        <div class="example">
            <h3>API to Database</h3>
            <pre><code><span class="cmd">fetch</span> <span class="str">"api/users"</span> | <span class="cmd">parse</span> json | <span class="cmd">get</span> <span class="str">"data"</span> | <span class="cmd">store</span> <span class="str">"users.db"</span></code></pre>
        </div>

        <div class="example">
            <h3>CSV Processing</h3>
            <pre><code><span class="cmd">read</span> <span class="str">"sales.csv"</span> | <span class="cmd">parse</span> csv | <span class="cmd">filter</span> <span class="str">"region"</span> <span class="str">"west"</span> | <span class="cmd">print</span></code></pre>
        </div>

        <div class="example">
            <h3>Data Pipeline</h3>
            <pre><code><span class="cmd">fetch</span> <span class="str">"api/metrics"</span> | <span class="cmd">parse</span> json | <span class="cmd">sort</span> <span class="str">"timestamp"</span> | <span class="cmd">take</span> 100 | <span class="cmd">write</span> <span class="str">"latest.json"</span></code></pre>
        </div>
    </div>

    <div class="section">
        <h2>Python vs XLG</h2>
        <div class="comparison">
            <div>
                <div class="label">Python (20+ lines)</div>
                <pre><code><span class="comment"># imports, request, error handling,</span>
<span class="comment"># json parsing, db connection,</span>
<span class="comment"># table creation, insert loop,</span>
<span class="comment"># commit, close...</span></code></pre>
            </div>
            <div>
                <div class="label">XLG (1 line)</div>
                <pre><code><span class="cmd">fetch</span> <span class="str">"url"</span> | <span class="cmd">parse</span> json | <span class="cmd">store</span> <span class="str">"data.db"</span></code></pre>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="install">
            <h2>Install</h2>
            <code>uv tool install xlg</code>
        </div>
    </div>
</body>
</html>
```

**Step 2: Commit**

```bash
mkdir -p site
git add site/index.html
git commit -m "feat: demo site with use cases"
```

---

## Task 23: Update README

**Files:**
- Modify: `README.md`

**Step 1: Update README**

```markdown
# XLG - eXpression LanGuage

Express complex operations in single commands.

## Install

```bash
uv tool install xlg
```

## Usage

```bash
xlg 'fetch "api/users" | parse json | print'
```

Or interactive REPL:

```bash
xlg
xlg> read "data.csv" | parse csv | filter "active" "true" | print
```

## Commands

**Sources:** `fetch`, `read`
**Transforms:** `parse`, `get`, `filter`, `sort`, `take`
**Sinks:** `print`, `write`, `store`

## Examples

```bash
# API to database
xlg 'fetch "api/users" | parse json | store "users.db"'

# CSV filtering
xlg 'read "data.csv" | parse csv | filter "region" "west" | print'

# JSON extraction
xlg 'fetch "api/data" | parse json | get "items" | take 10 | print'
```

## Development

```bash
just test   # run tests
just lint   # check code
just fmt    # format code
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: complete README with usage examples"
```

---

## Task 24: Final Integration Test

**Files:**
- Create: `tests/integration_test.py`

**Step 1: Write integration tests**

```python
"""End-to-end integration tests."""
import tempfile
from pathlib import Path
from xlg.lexer import tokenize
from xlg.parser import parse
from xlg.evaluator import evaluate


def run(source: str):
    return evaluate(parse(tokenize(source)))


def test_read_parse_filter_print(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,active\nalice,true\nbob,false\ncharlie,true")
        path = f.name
    result = run(f'read "{path}" | parse csv | filter "active" "true" | print')
    assert len(result) == 2
    assert result[0]["name"] == "alice"
    Path(path).unlink()


def test_full_pipeline():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"data": [{"name": "a"}, {"name": "b"}, {"name": "c"}]}')
        json_path = f.name
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    result = run(f'read "{json_path}" | parse json | get "data" | store "{db_path}"')
    assert result == 3
    Path(json_path).unlink()
    Path(db_path).unlink()
```

**Step 2: Run all tests**

Run: `just test`
Expected: All PASS

**Step 3: Commit**

```bash
mkdir -p tests
git add tests/integration_test.py
git commit -m "test: end-to-end integration tests"
```

---

Plan complete and saved to `docs/plans/2026-02-14-xlg-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
