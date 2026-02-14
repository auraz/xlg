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
