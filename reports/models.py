"""Models used by the executive report pipeline."""

from typing import Annotated, TypedDict

from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Required


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


class SensorMetric(TypedDict):
    """Daily sensor-type metrics aggregated across reporting farms."""

    sensor_type_id: int
    sensor_name: str
    unit: str
    farms_reporting: int
    farms_with_anomalies: int
    reading_count: int
    average_value: float | None
    min_value: float | None
    max_value: float | None
    anomaly_count: int
    anomaly_rate: float | None
    in_range_count: int
    in_range_rate: float | None


class ReportState(TypedDict, total=False):
    """State passed between LangGraph report stages."""

    report_date: Required[str]
    metrics: ExecutiveMetrics
    top_farms: list[TopFarm]
    top_rank: int | None
    top_rank_count: int
    sensor_metrics: list[SensorMetric]
    narrative: str
    sensor_analysis: str
    insights: list[str]
    html: str
    published_bucket: str
    object_key: str
    email_sent: bool


Insight = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=220,
    ),
]


class ReportSummary(BaseModel):
    """Structured summary returned by the local language model."""

    narrative: str = Field(min_length=1, max_length=1400)
    sensor_analysis: str = Field(min_length=1, max_length=900)
    insights: list[Insight] = Field(min_length=1, max_length=3)
