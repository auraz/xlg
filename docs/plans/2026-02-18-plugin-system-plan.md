# Plugin System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable custom XLG commands via plugins, starting with an AI-powered form-fill command.

**Architecture:** Plugins are Python files in `~/.config/xlg/plugins/`. Each exports `register(registry)` which adds commands. The evaluator loads plugins at startup and merges them with built-in commands.

**Tech Stack:** Python 3.12+, Playwright (browser automation), Anthropic SDK (Claude API)

---

## Task 1: Plugin Registry

**Files:**
- Create: `xlg/plugins.py`
- Test: `xlg/plugins_test.py`

**Step 1: Write the failing test**

```python
"""Plugin registry tests."""

from xlg.plugins import Registry


def test_registry_add_sink():
    registry = Registry()
    registry.add_sink("test", lambda data, arg: None)
    assert "test" in registry.sinks


def test_registry_add_source():
    registry = Registry()
    registry.add_source("test", lambda arg: iter([]))
    assert "test" in registry.sources


def test_registry_add_transform():
    registry = Registry()
    registry.add_transform("test", lambda stream, arg: stream)
    assert "test" in registry.transforms
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/plugins_test.py -v`
Expected: FAIL with "No module named 'xlg.plugins'"

**Step 3: Write minimal implementation**

```python
"""Plugin system for XLG custom commands."""

from typing import Any, Callable
from collections.abc import Generator


class Registry:
    """Registry for plugin commands."""

    def __init__(self) -> None:
        self.sources: dict[str, Callable] = {}
        self.transforms: dict[str, Callable] = {}
        self.sinks: dict[str, Callable] = {}

    def add_source(self, name: str, fn: Callable[..., Generator[Any, None, None]]) -> None:
        """Register a source command."""
        self.sources[name] = fn

    def add_transform(self, name: str, fn: Callable[..., Generator[Any, None, None]]) -> None:
        """Register a transform command."""
        self.transforms[name] = fn

    def add_sink(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a sink command."""
        self.sinks[name] = fn
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/plugins_test.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/plugins.py xlg/plugins_test.py
git commit -m "feat: add plugin registry"
```

---

## Task 2: Plugin Loader

**Files:**
- Modify: `xlg/plugins.py`
- Test: `xlg/plugins_test.py`

**Step 1: Write the failing test**

```python
def test_load_plugins_from_directory(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "test_plugin.py"
    plugin_file.write_text("""
def register(registry):
    registry.add_sink("test_cmd", lambda data, arg: "ok")
""")
    registry = Registry()
    load_plugins(registry, plugin_dir)
    assert "test_cmd" in registry.sinks


def test_load_plugins_handles_missing_dir(tmp_path):
    registry = Registry()
    load_plugins(registry, tmp_path / "nonexistent")
    assert len(registry.sinks) == 0
```

Add import at top: `from xlg.plugins import Registry, load_plugins`

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/plugins_test.py::test_load_plugins_from_directory -v`
Expected: FAIL with "cannot import name 'load_plugins'"

**Step 3: Write minimal implementation**

Add to `xlg/plugins.py`:

```python
import importlib.util
from pathlib import Path


def load_plugins(registry: Registry, plugin_dir: Path) -> None:
    """Load all plugins from directory."""
    if not plugin_dir.exists():
        return
    for plugin_path in plugin_dir.glob("*.py"):
        spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(registry)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/plugins_test.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/plugins.py xlg/plugins_test.py
git commit -m "feat: add plugin loader"
```

---

## Task 3: Integrate Plugins into Evaluator

**Files:**
- Modify: `xlg/evaluator.py`
- Test: `xlg/evaluator_test.py`

**Step 1: Write the failing test**

Add to `xlg/evaluator_test.py`:

```python
def test_evaluate_plugin_sink(tmp_path, monkeypatch):
    from xlg.parser import parse
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "echo.py"
    plugin_file.write_text("""
def register(registry):
    registry.add_sink("echo", lambda data, msg: f"echoed: {msg}")
""")
    monkeypatch.setenv("XLG_PLUGIN_DIR", str(plugin_dir))
    ast = parse('echo "hello"')
    result = evaluate(ast)
    assert result == "echoed: hello"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/evaluator_test.py::test_evaluate_plugin_sink -v`
Expected: FAIL with "Unknown command: echo"

**Step 3: Write minimal implementation**

Modify `xlg/evaluator.py`:

```python
"""Evaluator converts AST to executable pipeline."""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any
from xlg.parser import Pipeline
from xlg.commands.sources import cmd_read, cmd_fetch
from xlg.commands.discovery import cmd_reddit, cmd_hn, cmd_museum, cmd_github, cmd_wiki
from xlg.commands.transforms import cmd_parse, cmd_get, cmd_filter, cmd_take, cmd_sort, cmd_summarize
from xlg.commands.sinks import cmd_open, cmd_pause, cmd_play, cmd_previous, cmd_print, cmd_resume, cmd_skip, cmd_status, cmd_store, cmd_toggle, cmd_volume, cmd_write
from xlg.plugins import Registry, load_plugins


def _get_plugin_registry() -> Registry:
    """Load plugins from config directory."""
    registry = Registry()
    plugin_dir = Path(os.environ.get("XLG_PLUGIN_DIR", Path.home() / ".config" / "xlg" / "plugins"))
    load_plugins(registry, plugin_dir)
    return registry


def evaluate(ast: Pipeline, source: Generator | None = None) -> Any:
    """Evaluate a pipeline AST."""
    registry = _get_plugin_registry()
    stream = source
    for cmd in ast.commands:
        name, args = cmd.name, cmd.args
        if name == "read":
            stream = cmd_read(args[0])
        elif name == "fetch":
            stream = cmd_fetch(args[0])
        elif name == "reddit":
            stream = cmd_reddit(args[0], args[1] if len(args) > 1 else "")
        elif name == "hn":
            stream = cmd_hn(args[0])
        elif name == "museum":
            stream = cmd_museum(args[0], args[1])
        elif name == "github":
            stream = cmd_github(args[0])
        elif name == "wiki":
            stream = cmd_wiki(args[0] if args else "")
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
        elif name == "summarize":
            stream = cmd_summarize(stream)
        elif name == "print":
            return cmd_print(stream)
        elif name == "write":
            return cmd_write(stream, args[0])
        elif name == "store":
            return cmd_store(stream, args[0])
        elif name == "play":
            return cmd_play(args[0])
        elif name == "pause":
            return cmd_pause()
        elif name == "resume":
            return cmd_resume()
        elif name == "toggle":
            return cmd_toggle()
        elif name == "skip":
            return cmd_skip()
        elif name == "previous":
            return cmd_previous()
        elif name == "volume":
            return cmd_volume(args[0])
        elif name == "status":
            return cmd_status()
        elif name == "open":
            return cmd_open(stream)
        elif name in registry.sources:
            stream = registry.sources[name](*args)
        elif name in registry.transforms:
            stream = registry.transforms[name](stream, *args)
        elif name in registry.sinks:
            return registry.sinks[name](stream, *args)
        else:
            raise ValueError(f"Unknown command: {name}")
    return list(stream) if stream else []
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/evaluator_test.py::test_evaluate_plugin_sink -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/evaluator.py xlg/evaluator_test.py
git commit -m "feat: integrate plugins into evaluator"
```

---

## Task 4: Add Dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add playwright and anthropic dependencies**

```toml
dependencies = [
    "feedparser>=6.0.12",
    "httpx>=0.27",
    "openai>=2.21.0",
    "xlg-player",
    "playwright>=1.40",
    "anthropic>=0.40",
]
```

**Step 2: Install dependencies**

Run: `uv sync`
Expected: Dependencies installed

**Step 3: Install playwright browsers**

Run: `uv run playwright install chromium`
Expected: Chromium browser installed

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add playwright and anthropic dependencies"
```

---

## Task 5: Fill Plugin - Config Loading

**Files:**
- Create: `xlg/plugins/fill.py` (example plugin, shipped with xlg)
- Test: `xlg/plugins/fill_test.py`

**Step 1: Write the failing test**

```python
"""Fill plugin tests."""

import json
from xlg.plugins.fill import load_sites, load_profile, resolve_target


def test_load_sites(tmp_path):
    sites_file = tmp_path / "sites.json"
    sites_file.write_text('{"amazon": "https://amazon.com/checkout"}')
    sites = load_sites(sites_file)
    assert sites["amazon"] == "https://amazon.com/checkout"


def test_load_profile(tmp_path):
    profile_file = tmp_path / "profile.json"
    profile_file.write_text('{"name": "John", "zip": "90210"}')
    profile = load_profile(profile_file)
    assert profile["name"] == "John"


def test_resolve_target_alias(tmp_path):
    sites_file = tmp_path / "sites.json"
    sites_file.write_text('{"amazon": "https://amazon.com/checkout"}')
    url = resolve_target("amazon", sites_file)
    assert url == "https://amazon.com/checkout"


def test_resolve_target_url():
    url = resolve_target("https://example.com", None)
    assert url == "https://example.com"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/plugins/fill_test.py -v`
Expected: FAIL with "No module named 'xlg.plugins.fill'"

**Step 3: Write minimal implementation**

Create `xlg/plugins/__init__.py`:
```python
"""XLG plugins package."""
```

Create `xlg/plugins/fill.py`:
```python
"""Fill plugin - AI-powered form filling."""

import json
from pathlib import Path
from typing import Any


def load_sites(path: Path) -> dict[str, str]:
    """Load site aliases from JSON file."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def load_profile(path: Path) -> dict[str, Any]:
    """Load user profile from JSON file."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def resolve_target(target: str, sites_path: Path | None) -> str:
    """Resolve target to URL - either alias lookup or direct URL."""
    if target.startswith("http://") or target.startswith("https://"):
        return target
    if sites_path:
        sites = load_sites(sites_path)
        if target in sites:
            return sites[target]
    raise ValueError(f"Unknown site alias: {target}")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/plugins/fill_test.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/plugins/__init__.py xlg/plugins/fill.py xlg/plugins/fill_test.py
git commit -m "feat: add fill plugin config loading"
```

---

## Task 6: Fill Plugin - HTML Extraction

**Files:**
- Modify: `xlg/plugins/fill.py`
- Test: `xlg/plugins/fill_test.py`

**Step 1: Write the failing test**

```python
def test_extract_form_html():
    html = """
    <html>
    <body>
        <header>Nav</header>
        <form id="checkout">
            <input name="name" type="text">
            <input name="zip" type="text">
        </form>
        <footer>Footer</footer>
    </body>
    </html>
    """
    form_html = extract_form_html(html)
    assert "<form" in form_html
    assert 'name="name"' in form_html
    assert "<header>" not in form_html
```

Add import: `from xlg.plugins.fill import load_sites, load_profile, resolve_target, extract_form_html`

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/plugins/fill_test.py::test_extract_form_html -v`
Expected: FAIL with "cannot import name 'extract_form_html'"

**Step 3: Write minimal implementation**

Add to `xlg/plugins/fill.py`:

```python
import re


def extract_form_html(html: str) -> str:
    """Extract form elements from HTML, removing noise."""
    forms = re.findall(r"<form[^>]*>.*?</form>", html, re.DOTALL | re.IGNORECASE)
    return "\n".join(forms) if forms else html[:5000]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/plugins/fill_test.py::test_extract_form_html -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/plugins/fill.py xlg/plugins/fill_test.py
git commit -m "feat: add HTML form extraction"
```

---

## Task 7: Fill Plugin - Claude Field Mapping

**Files:**
- Modify: `xlg/plugins/fill.py`
- Test: `xlg/plugins/fill_test.py`

**Step 1: Write the failing test**

```python
def test_map_fields_with_claude(mocker):
    mock_client = mocker.MagicMock()
    mock_client.messages.create.return_value.content = [mocker.MagicMock(text='{"#name": "John", "#zip": "90210"}')]
    profile = {"name": "John", "zip": "90210"}
    form_html = '<form><input id="name"><input id="zip"></form>'
    mappings = map_fields_with_claude(mock_client, form_html, profile)
    assert mappings == {"#name": "John", "#zip": "90210"}
```

Add import: `from xlg.plugins.fill import load_sites, load_profile, resolve_target, extract_form_html, map_fields_with_claude`

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/plugins/fill_test.py::test_map_fields_with_claude -v`
Expected: FAIL with "cannot import name 'map_fields_with_claude'"

**Step 3: Write minimal implementation**

Add to `xlg/plugins/fill.py`:

```python
import anthropic


def map_fields_with_claude(client: anthropic.Anthropic, form_html: str, profile: dict[str, Any]) -> dict[str, str]:
    """Use Claude to map profile data to form fields."""
    prompt = f"""Analyze this HTML form and map the user's profile data to form fields.

Form HTML:
{form_html}

User Profile:
{json.dumps(profile, indent=2)}

Return ONLY a JSON object mapping CSS selectors to values. Example:
{{"#field-id": "value", "[name='field']": "value"}}

Use the most specific selector available (id > name > other attributes).
Only include fields that have matching profile data."""

    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1024, messages=[{"role": "user", "content": prompt}])
    return json.loads(response.content[0].text)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/plugins/fill_test.py::test_map_fields_with_claude -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/plugins/fill.py xlg/plugins/fill_test.py
git commit -m "feat: add Claude field mapping"
```

---

## Task 8: Fill Plugin - Browser Automation

**Files:**
- Modify: `xlg/plugins/fill.py`
- Test: `xlg/plugins/fill_test.py`

**Step 1: Write the failing test**

```python
def test_fill_form_fields(mocker):
    mock_page = mocker.MagicMock()
    mappings = {"#name": "John", "#zip": "90210"}
    fill_form_fields(mock_page, mappings)
    assert mock_page.fill.call_count == 2
    mock_page.fill.assert_any_call("#name", "John")
    mock_page.fill.assert_any_call("#zip", "90210")
```

Add import: `from xlg.plugins.fill import load_sites, load_profile, resolve_target, extract_form_html, map_fields_with_claude, fill_form_fields`

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/plugins/fill_test.py::test_fill_form_fields -v`
Expected: FAIL with "cannot import name 'fill_form_fields'"

**Step 3: Write minimal implementation**

Add to `xlg/plugins/fill.py`:

```python
from playwright.sync_api import Page


def fill_form_fields(page: Page, mappings: dict[str, str]) -> None:
    """Fill form fields using Playwright."""
    for selector, value in mappings.items():
        page.fill(selector, value)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/plugins/fill_test.py::test_fill_form_fields -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/plugins/fill.py xlg/plugins/fill_test.py
git commit -m "feat: add Playwright form filling"
```

---

## Task 9: Fill Plugin - Main Command

**Files:**
- Modify: `xlg/plugins/fill.py`
- Test: `xlg/plugins/fill_test.py`

**Step 1: Write the failing test**

```python
def test_cmd_fill_integration(tmp_path, mocker):
    sites_file = tmp_path / "data" / "sites.json"
    profile_file = tmp_path / "data" / "profile.json"
    sites_file.parent.mkdir(parents=True)
    sites_file.write_text('{"test": "https://example.com/form"}')
    profile_file.write_text('{"name": "John"}')
    mocker.patch.dict("os.environ", {"XLG_CONFIG_DIR": str(tmp_path)})
    mock_playwright = mocker.patch("xlg.plugins.fill.sync_playwright")
    mock_browser = mocker.MagicMock()
    mock_page = mocker.MagicMock()
    mock_page.content.return_value = "<form><input id='name'></form>"
    mock_browser.new_page.return_value = mock_page
    mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
    mock_claude = mocker.patch("xlg.plugins.fill.anthropic.Anthropic")
    mock_claude.return_value.messages.create.return_value.content = [mocker.MagicMock(text='{"#name": "John"}')]
    result = cmd_fill(None, "test")
    assert "filled" in result.lower()
```

Add import: `from xlg.plugins.fill import cmd_fill`

**Step 2: Run test to verify it fails**

Run: `uv run pytest xlg/plugins/fill_test.py::test_cmd_fill_integration -v`
Expected: FAIL with "cannot import name 'cmd_fill'"

**Step 3: Write minimal implementation**

Add to `xlg/plugins/fill.py`:

```python
import os
from playwright.sync_api import sync_playwright


def cmd_fill(data: Any, target: str) -> str:
    """Fill a web form using AI-assisted field mapping."""
    config_dir = Path(os.environ.get("XLG_CONFIG_DIR", Path.home() / ".config" / "xlg"))
    sites_path = config_dir / "data" / "sites.json"
    profile_path = config_dir / "data" / "profile.json"
    url = resolve_target(target, sites_path)
    profile = load_profile(profile_path)
    if not profile:
        raise ValueError(f"No profile found at {profile_path}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        html = page.content()
        form_html = extract_form_html(html)
        client = anthropic.Anthropic()
        mappings = map_fields_with_claude(client, form_html, profile)
        fill_form_fields(page, mappings)
        input("Form filled. Press Enter to close browser...")
        browser.close()
    return f"Filled {len(mappings)} fields"


def register(registry: "Registry") -> None:
    """Register fill command with XLG."""
    registry.add_sink("fill", cmd_fill)
```

Add import at top: `from xlg.plugins import Registry`

**Step 4: Run test to verify it passes**

Run: `uv run pytest xlg/plugins/fill_test.py::test_cmd_fill_integration -v`
Expected: PASS

**Step 5: Commit**

```bash
git add xlg/plugins/fill.py xlg/plugins/fill_test.py
git commit -m "feat: add fill command main function"
```

---

## Task 10: Auto-register Built-in Plugins

**Files:**
- Modify: `xlg/evaluator.py`

**Step 1: Modify evaluator to load built-in plugins**

Update `_get_plugin_registry()` in `xlg/evaluator.py`:

```python
def _get_plugin_registry() -> Registry:
    """Load plugins from config directory and built-in plugins."""
    registry = Registry()
    from xlg.plugins.fill import register as fill_register
    fill_register(registry)
    plugin_dir = Path(os.environ.get("XLG_PLUGIN_DIR", Path.home() / ".config" / "xlg" / "plugins"))
    load_plugins(registry, plugin_dir)
    return registry
```

**Step 2: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add xlg/evaluator.py
git commit -m "feat: auto-register built-in fill plugin"
```

---

## Task 11: Update README

**Files:**
- Modify: `README.md`

**Step 1: Add fill command documentation**

Add after Play Setup section:

```markdown
## Fill Setup (AI Form Filling)

Automate checkout forms using Claude AI.

1. Set API key:

```bash
export ANTHROPIC_API_KEY="your-key"
```

2. Create profile:

```bash
mkdir -p ~/.config/xlg/data
cat > ~/.config/xlg/data/profile.json << 'EOF'
{
  "name": "Your Name",
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "zip": "94102"
}
EOF
```

3. Add site aliases:

```bash
cat > ~/.config/xlg/data/sites.json << 'EOF'
{
  "amazon": "https://amazon.com/checkout"
}
EOF
```

4. Usage:

```bash
xlg 'fill "amazon"'           # fill form using alias
xlg 'fill "https://..."'      # fill form at URL
```

Browser opens, Claude analyzes the form, fields are filled. Review and submit manually.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add fill command setup instructions"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Plugin Registry class |
| 2 | Plugin loader from directory |
| 3 | Integrate plugins into evaluator |
| 4 | Add playwright/anthropic dependencies |
| 5 | Fill plugin config loading |
| 6 | HTML form extraction |
| 7 | Claude field mapping |
| 8 | Playwright form filling |
| 9 | Fill command main function |
| 10 | Auto-register built-in plugins |
| 11 | Update README |
