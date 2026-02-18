"""Fill plugin - AI-powered form filling."""

import json
import re
from pathlib import Path
from typing import Any

import anthropic


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
