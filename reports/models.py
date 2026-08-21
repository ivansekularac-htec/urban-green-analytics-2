"""Models used by the executive report pipeline."""

from typing import Required, TypedDict

from pydantic import BaseModel, Field


class ExecutiveMetrics(TypedDict):
    """Executive KPI values calculated for one report date."""

    farms_reporting: int
    total_yield_kg: float
    harvest_count: int
    premium_yield_kg: float
    premium_yield_share: float | None
    energy_kwh: float
    energy_efficiency_kwh_per_kg: float | None
    reading_count: int
    anomaly_count: int
    sensor_anomaly_rate: float | None


class TopFarm(TypedDict):
    """Top-ranked farm values for one report date."""

    rank: int
    farm_name: str
    total_yield_kg: float
    premium_yield_share: float | None
    energy_efficiency_kwh_per_kg: float | None
    composite_score: float


class ReportState(TypedDict, total=False):
    """State passed between LangGraph report stages."""

    report_date: Required[str]
    metrics: ExecutiveMetrics
    top_farms: list[TopFarm]
    top_rank: int | None
    top_rank_count: int
    narrative: str
    insights: list[str]
    html: str
    published_bucket: str
    object_key: str
    email_sent: bool


class ReportSummary(BaseModel):
    """Structured summary returned by the local language model."""

    narrative_production: str = Field(min_length=1)
    narrative_energy: str = Field(min_length=1)
    premium_insight: str = Field(min_length=1)
    leaderboard_insight: str = Field(min_length=1)
    sensor_insight: str = Field(min_length=1)
