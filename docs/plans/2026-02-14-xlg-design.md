# XLG - eXpression LanGuage Design

## Overview

XLG is a shell-like programming language for expressing complex multi-step operations in single commands. It leverages modern computing power to provide high-level primitives for common application development tasks.

## Core Concept

```
fetch "api.example.com/users" | parse json | store "users.db"
```

One line replaces 20+ lines of Python: HTTP request, JSON parsing, database storage.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        XLG                              │
├─────────────────────────────────────────────────────────┤
│  REPL / Script Runner                                   │
├─────────────────────────────────────────────────────────┤
│  Parser (text → AST)                                    │
├─────────────────────────────────────────────────────────┤
│  Evaluator (AST → Pipeline)                             │
├─────────────────────────────────────────────────────────┤
│  Pipeline Engine (generators + executors)               │
├─────────────────────────────────────────────────────────┤
│  Built-in Commands                                      │
└─────────────────────────────────────────────────────────┘
```

**Pipeline-First**: Everything is a stream. Commands are transformers. Built on Python generators for lazy evaluation and memory efficiency.

## Syntax

```
fetch "url" | parse json | store "users.db"
read "data.csv" | transform double | write "output.csv"
fetch "url" | parse json | get "data.items" | store "items.db"
```

**Rules**:
- Pipes chain commands left-to-right
- Commands take only positional string/number arguments
- No variables, no flags, no inline expressions
- Named transforms instead of inline lambdas

**Literals**: `"string"`, `123`

## Data Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  fetch  │ --> │  parse  │ --> │  store  │
│ yields  │     │ yields  │     │consumes │
│ bytes   │     │ objects │     │ objects │
└─────────┘     └─────────┘     └─────────┘
```

**Data types**:
- `bytes` - raw data from fetch/read
- `text` - string content
- `object` - parsed dict/map
- `list` - collection of items
- `table` - rows with columns

**Behavior**:
- Each command is a Python generator
- Data streams lazily
- Pipeline terminates at sink command
- Commands auto-detect input type

## Error Handling

Fail fast, fail clearly. No fallbacks.

```
fetch "bad-url" | parse json | store "db"
       ↓
Error: fetch failed - connection refused
  at: fetch "bad-url"
```

- Pipeline stops on first error
- Error shows which command failed and why
- Exit code non-zero on error

## Built-in Commands

### Sources
| Command | Description |
|---------|-------------|
| `fetch "url"` | HTTP GET, yields bytes |
| `read "path"` | Read file(s), yields content |
| `query "sql" "db"` | Query database, yields rows |

### Transforms
| Command | Description |
|---------|-------------|
| `parse json/csv/xml` | Parse bytes into structured data |
| `get "path"` | Extract nested field |
| `filter "field" "value"` | Keep matching items |
| `transform name` | Apply named transform |
| `sort "field"` | Sort by field |
| `take 10` | Limit to N items |

### Sinks
| Command | Description |
|---------|-------------|
| `store "path.db"` | Save to SQLite |
| `write "path"` | Write to file |
| `visualize bar/line/table` | Render chart or table |
| `deploy "target"` | Deploy to S3, server, etc. |
| `print` | Output to stdout |

## Project Structure

```
xlg/
  __init__.py
  main.py              # CLI entry, REPL
  lexer.py             # Tokenizer
  parser.py            # AST builder
  evaluator.py         # Pipeline builder
  pipeline.py          # Generator chaining
  commands/
    __init__.py
    sources.py         # fetch, read, query
    transforms.py      # parse, get, filter, transform, sort, take
    sinks.py           # store, write, visualize, deploy, print
  transforms/
    __init__.py
    builtins.py        # double, uppercase, lowercase, etc.
site/
  index.html           # Promotional demo page
docs/
  plans/
README.md
justfile
pyproject.toml
```

## Testing

Tests live alongside modules:
```
xlg/
  lexer.py
  lexer_test.py
  parser.py
  parser_test.py
  ...
```

- Unit tests for lexer, parser, evaluator
- Each command tested in isolation
- Integration tests for end-to-end pipelines

## Demo Site

Single-page promotional site with:
- Hero: "XLG - Express more in one line"
- Live examples with syntax highlighting
- Use cases showing Python vs XLG comparison
- Install instructions
- Clean, modern, dark theme

## Implementation

- **Language**: Python
- **Type system**: Dynamic
- **Extensibility**: Not initially - focus on powerful built-ins
