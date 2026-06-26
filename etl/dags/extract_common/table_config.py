from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final


@dataclass(frozen=True)
class ExtractTable:
    """Configuration for one incremental Postgres app.* table extract."""

    name: str
    schedule: str
    schema: str = "app"
    primary_key: str = "id"
    cursor_column: str = "updated_at"
    partition_column: str | None = None
    partition_name: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Return a JSON-serializable representation for Airflow operator kwargs."""
        return asdict(self)


DAILY: Final[str] = "@daily"
HOURLY: Final[str] = "@hourly"


APP_TABLES: Final[tuple[ExtractTable, ...]] = (
    ExtractTable(name="roles", schedule=DAILY),
    ExtractTable(name="quality_grades", schedule=DAILY),
    ExtractTable(name="farm_infrastructure_types", schedule=DAILY),
    ExtractTable(name="growing_system_types", schedule=DAILY),
    ExtractTable(name="crop_categories", schedule=DAILY),
    ExtractTable(name="sensor_types", schedule=DAILY),
    ExtractTable(name="farms", schedule=DAILY),
    ExtractTable(name="users", schedule=DAILY),
    ExtractTable(name="crops", schedule=DAILY),
    ExtractTable(name="user_roles", schedule=DAILY),
    ExtractTable(name="farm_crops", schedule=DAILY),
    ExtractTable(name="sensors", schedule=DAILY),
    # The current schema has no dedicated harvested_at / harvest_date column.
    # created_at is therefore used as the harvest business-date partition.
    ExtractTable(
        name="harvests",
        schedule=HOURLY,
        partition_column="created_at",
        partition_name="harvest_date",
    ),
)
