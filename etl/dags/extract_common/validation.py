from __future__ import annotations

import re
from typing import Any, Final

IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z_][a-z0-9_]*$")


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": config.get("schema") or "app",
        "name": config["name"],
        "primary_key": config.get("primary_key") or "id",
        "cursor_column": config.get("cursor_column") or "updated_at",
        "partition_column": config.get("partition_column"),
        "partition_name": config.get("partition_name"),
    }


def validate_config(config: dict[str, Any]) -> None:
    identifiers = [
        config["schema"],
        config["name"],
        config["primary_key"],
        config["cursor_column"],
    ]

    if config.get("partition_column"):
        identifiers.append(config["partition_column"])

    if config.get("partition_name"):
        identifiers.append(config["partition_name"])

    invalid_identifiers = [
        value for value in identifiers if not IDENTIFIER_PATTERN.fullmatch(value)
    ]

    if invalid_identifiers:
        raise ValueError(f"Invalid SQL/object-key identifiers: {invalid_identifiers}")