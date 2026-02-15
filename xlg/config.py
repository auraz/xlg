"""Config file support for xlg."""

import os
from pathlib import Path


def load_config() -> dict[str, str]:
    """Load config from ~/.config/xlg/config file."""
    config_path = Path.home() / ".config" / "xlg" / "config"
    config = {}
    if config_path.exists():
        for line in config_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def get_config(key: str, default: str = "") -> str:
    """Get config value, checking config file first, then env var."""
    config = load_config()
    return config.get(key) or os.environ.get(key) or default
