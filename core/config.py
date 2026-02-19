from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path("configs/sites")


def load_site_configs() -> list[dict[str, Any]]:
    sites: list[dict[str, Any]] = []
    for path in sorted(CONFIG_DIR.glob("*.json")):
        sites.append(json.loads(path.read_text(encoding="utf-8")))
    return sites
