"""Fill plugin - AI-powered form filling."""

import json
import os
import re
from pathlib import Path
from typing import Any

import anthropic
from playwright.sync_api import Page, sync_playwright


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


def extract_form_html(html: str) -> str:
    """Extract form elements from HTML, removing noise."""
    forms = re.findall(r"<form[^>]*>.*?</form>", html, re.DOTALL | re.IGNORECASE)
    return "\n".join(forms) if forms else html[:5000]


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


def fill_form_fields(page: Page, mappings: dict[str, str]) -> None:
    """Fill form fields using Playwright."""
    for selector, value in mappings.items():
        page.fill(selector, value)


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


def register(registry: Any) -> None:
    """Register fill command with XLG."""
    registry.add_sink("fill", cmd_fill)
