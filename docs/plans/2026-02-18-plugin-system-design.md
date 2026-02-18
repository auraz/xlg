# XLG Plugin System Design

## Goal

Enable custom commands via plugins, starting with a form-fill command that uses AI to automate shopping checkout.

## Plugin System Architecture

```
~/.config/xlg/
├── config                    # existing credentials
├── plugins/                  # plugin directory
│   ├── fill.py              # form-fill plugin
│   └── ...                  # future plugins
└── data/
    ├── sites.json           # site aliases
    └── profile.json         # personal data for forms
```

**Loading flow:**
1. XLG starts → scans `~/.config/xlg/plugins/*.py`
2. Each plugin's `register(registry)` function called
3. Plugin adds commands to registry
4. Commands available in XLG expressions

## Plugin Interface

```python
# ~/.config/xlg/plugins/fill.py
from xlg.plugins import Registry

def register(registry: Registry) -> None:
    registry.add_sink("fill", fill_form)

def fill_form(data: Any, target: str) -> None:
    """Fill form - target is alias or URL."""
    ...
```

**Registry methods:**
- `add_source(name, fn)` - commands that produce data
- `add_transform(name, fn)` - commands that modify data
- `add_sink(name, fn)` - commands that consume data

## Fill Command

**Usage:**
```bash
xlg 'fill "amazon"'      # resolves alias to URL
xlg 'fill "https://..."' # direct URL
```

**Config files:**

```json
// ~/.config/xlg/data/sites.json
{
  "amazon": "https://amazon.com/checkout",
  "costco": "https://costco.com/CheckoutCartDisplayView",
  "newegg": "https://newegg.com/checkout"
}
```

```json
// ~/.config/xlg/data/profile.json
{
  "name": "...",
  "address": "...",
  "city": "...",
  "zip": "...",
  "card_last4": "1234"
}
```

## AI Form Analysis

1. Playwright opens URL → extracts page HTML
2. Claude analyzes HTML → identifies form fields
3. Claude maps profile data → matches data to fields
4. Playwright fills fields → types values into inputs

**Claude returns:**
```json
{
  "#shipping-name": "John Doe",
  "#address-line1": "123 Main St",
  "[name='zipcode']": "90210"
}
```

No pre-defined selectors - Claude figures it out dynamically.

## Execution Flow

```
xlg 'fill "amazon"'
    │
    ├─→ Load sites.json → resolve alias → URL
    ├─→ Load profile.json → user data
    │
    ├─→ Playwright: launch browser, navigate to URL
    ├─→ Extract page HTML (forms only)
    │
    ├─→ Claude: analyze HTML + profile → field mappings
    │
    ├─→ Playwright: fill each field, pause before submit
    │
    └─→ User reviews, manually clicks submit
```

**Key behaviors:**
- No auto-submit - pauses for user to review
- Visible browser - not headless
- Uses `ANTHROPIC_API_KEY` for Claude

## Dependencies

- `playwright` - browser automation
- `anthropic` - Claude API

## Files to Create

- `xlg/plugins.py` - registry and loader
- `~/.config/xlg/plugins/fill.py` - the fill command
- `~/.config/xlg/data/sites.json` - site aliases
- `~/.config/xlg/data/profile.json` - personal data
