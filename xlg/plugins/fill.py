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
