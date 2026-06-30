from __future__ import annotations

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).with_name("tables.yaml")


def load_tables() -> list[dict]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config["tables"]


TABLES = load_tables()
