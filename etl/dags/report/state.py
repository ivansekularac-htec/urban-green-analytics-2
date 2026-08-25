"""State definitions for the executive report pipeline."""

from typing import TypedDict


class ExecutiveMetrics(TypedDict):
    """Headline metrics used in the executive report."""

    reporting_farms: int
    total_harvest_yield_kg: float | None
    total_energy_kwh: float | None
    energy_efficiency_kwh_per_kg: float | None
    waste_reduction_progress: float | None
    environmental_compliance_rate: float | None
    sensor_anomaly_rate: float | None
    total_sensor_readings: int | None


class TopFarm(TypedDict):
    """One farm from the daily performance leaderboard."""

    rank: int
    farm: str
    city: str
    total_yield_kg: float | None
    premium_yield_share: float | None
    energy_efficiency_kwh_per_kg: float | None


class SensorOverview(TypedDict):
    """Daily aggregate for one sensor type."""

    sensor_type: str | None
    unit: str | None
    readings: int
    anomalies: int
    anomaly_rate: float | None
    compliance_rate: float | None


class ReportState(TypedDict, total=False):
    """Shared state passed through the LangGraph report pipeline."""

    report_date: str
    metrics: ExecutiveMetrics
    top_farms: list[TopFarm]
    sensors: list[SensorOverview]
    narrative: str
    insights: list[str]
    html: str
    object_key: str
