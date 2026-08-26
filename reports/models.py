"""Shared state and data models for the executive report graph."""

from datetime import date
from typing import Annotated, TypedDict

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class ExecutiveMetrics(TypedDict):
    """Fixed executive KPI values retrieved for one report date."""

    farms_reporting: int
    total_yield_kg: float
    harvest_count: int
    premium_yield_kg: float
    premium_yield_share: float | None
    energy_kwh: float
    energy_efficiency_kwh_per_kg: float | None
    reading_count: int
    anomaly_count: int
    anomaly_rate: float | None


class TopFarm(TypedDict):
    """One precomputed farm leaderboard entry for the report date."""

    rank: int
    farm_name: str
    total_yield_kg: float
    premium_yield_share: float | None
    energy_efficiency_kwh_per_kg: float | None
    composite_score: float


Narrative = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=800),
]
Insight = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=240),
]


class ReportSummary(BaseModel):
    """Validated, length-bounded content returned by the local model."""

    model_config = ConfigDict(extra="forbid")

    narrative: Narrative
    insights: list[Insight] = Field(min_length=3, max_length=4)


class ReportState(TypedDict, total=False):
    """State accumulated as the report moves through the LangGraph stages."""

    report_date: date
    metrics: ExecutiveMetrics
    top_farms: list[TopFarm]
    summary: ReportSummary
    html: str
    published_bucket: str
    object_key: str
    email_sent: bool
