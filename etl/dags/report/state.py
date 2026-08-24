"""The state passed along the report graph.

Each node adds its own keys and leaves the rest untouched, so the shape grows
from `report_date` at the start to a full report by `store`. `summary_source`
records whether the narrative came from the model or the fallback, so a degraded
run is visible rather than looking identical to a real one.
"""

from __future__ import annotations

from typing import TypedDict


class ReportState(TypedDict, total=False):
    """The graph's working state.

    Only `report_date` is required to start; every other key is filled by a
    node. `total=False` keeps the intermediate states valid before the keys
    that later nodes add exist yet.
    """

    report_date: str  # YYYY-MM-DD, the day the report covers

    kpis: dict  # headline figures from the warehouse
    has_data: bool  # False when the date has no loaded metrics

    narrative: str  # the model's prose, or the fallback
    insights: list[str]  # a few bullet points
    summary_source: str  # "model" or "fallback"

    html: str  # the rendered, self-contained document
    object_key: str  # where it was stored in the bucket
    email_sent: bool  # whether the email left for the sink
