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


def load_site_data(config_dir: Path, site_name: str) -> dict[str, Any]:
    """Load saved data for a specific site."""
    site_file = config_dir / "data" / "saved" / f"{site_name}.json"
    if not site_file.exists():
        return {}
    return json.loads(site_file.read_text())


def save_site_data(config_dir: Path, site_name: str, data: dict[str, Any]) -> None:
    """Save data for a specific site."""
    saved_dir = config_dir / "data" / "saved"
    saved_dir.mkdir(parents=True, exist_ok=True)
    site_file = saved_dir / f"{site_name}.json"
    site_file.write_text(json.dumps(data, indent=2))


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


def analyze_form_fields(client: anthropic.Anthropic, form_html: str) -> list[dict[str, str]]:
    """Analyze form to identify all fillable fields."""
    prompt = f"""Analyze this HTML form and identify all fillable fields.

Form HTML:
{form_html}

Return ONLY a JSON array of objects, each with:
- "selector": CSS selector for the field
- "name": human-readable field name (e.g., "First Name", "Tracking Number")
- "type": field type (text, email, phone, select, etc.)

Example: [{{"selector": "#fname", "name": "First Name", "type": "text"}}]

Return ONLY valid JSON, no markdown, no explanation."""

    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=2048, messages=[{"role": "user", "content": prompt}])
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def prompt_missing_fields(fields: list[dict[str, str]], profile: dict[str, Any]) -> dict[str, Any]:
    """Prompt user for fields not in profile."""
    updated_profile = profile.copy()
    for field in fields:
        name = field["name"]
        key = name.lower().replace(" ", "_")
        if key not in profile and name.lower().replace(" ", "_") not in profile:
            value = input(f"{name}: ")
            if value:
                updated_profile[key] = value
    return updated_profile


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
Only include fields that have matching profile data.
Return ONLY valid JSON, no markdown, no explanation."""

    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1024, messages=[{"role": "user", "content": prompt}])
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def fill_form_fields(page: Page, mappings: dict[str, str]) -> None:
    """Fill form fields using Playwright."""
    for selector, value in mappings.items():
        page.fill(selector, value)


def get_site_name(target: str) -> str:
    """Extract site name from target for saving data."""
    if target.startswith("http://") or target.startswith("https://"):
        from urllib.parse import urlparse
        return urlparse(target).netloc.replace(".", "_")
    return target


def cmd_fill(data: Any, target: str) -> str:
    """Fill a web form using AI-assisted field mapping."""
    config_dir = Path(os.environ.get("XLG_CONFIG_DIR", Path.home() / ".config" / "xlg"))
    sites_path = config_dir / "data" / "sites.json"
    profile_path = config_dir / "data" / "profile.json"
    url = resolve_target(target, sites_path)
    site_name = get_site_name(target)
    profile = load_profile(profile_path)
    site_data = load_site_data(config_dir, site_name)
    combined = {**profile, **site_data}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        html = page.content()
        form_html = extract_form_html(html)
        client = anthropic.Anthropic()
        fields = analyze_form_fields(client, form_html)
        print(f"Found {len(fields)} form fields")
        filled = prompt_missing_fields(fields, combined)
        new_values = {k: v for k, v in filled.items() if k not in profile}
        if new_values:
            site_data.update(new_values)
            save_site_data(config_dir, site_name, site_data)
            print(f"Saved {len(new_values)} values for {site_name}")
        mappings = map_fields_with_claude(client, form_html, filled)
        fill_form_fields(page, mappings)
        input("Form filled. Press Enter to close browser...")
        browser.close()
    return f"Filled {len(mappings)} fields"


def register(registry: Any) -> None:
    """Register fill command with XLG."""
    registry.add_sink("fill", cmd_fill)
