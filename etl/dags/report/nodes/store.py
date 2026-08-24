"""Fourth node: store the document in the staging bucket.

The object is the one thing the ticket asks for, so this node does not soften a
failure into a warning: a failed write propagates and fails the run. The key is
deterministic, so re-running a date overwrites the same object instead of
adding a second one.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from report.deps import ReportDeps
from report.state import ReportState

logger = logging.getLogger(__name__)

_HTML_CONTENT_TYPE = "text/html; charset=utf-8"


def object_key(report_date: str) -> str:
    """The date-partitioned key a report is stored under.

    Pure and deterministic, so the same date always names the same object -
    which is what makes a re-run an overwrite rather than a duplicate.
    """
    return f"reports/executive/date={report_date}/report.html"


def make_store(deps: ReportDeps) -> Callable[[ReportState], dict]:
    """Build the store node against an S3 client and a bucket."""

    def store(state: ReportState) -> dict:
        key = object_key(state["report_date"])

        # No try/except: a failed write must fail the task, because the object
        # at this key is the deliverable. put_object overwrites by default, so a
        # re-run replaces the object rather than duplicating it.
        deps.s3.put_object(
            Bucket=deps.bucket,
            Key=key,
            Body=state["html"].encode("utf-8"),
            ContentType=_HTML_CONTENT_TYPE,
        )

        logger.info(f"stored report at {deps.bucket}/{key}")
        return {"object_key": key}

    return store
