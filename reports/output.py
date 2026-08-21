"""Render and publish UrbanGreen executive reports."""

import io
import logging
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    select_autoescape,
)
from minio import Minio

from reports.config import get_minio_settings
from reports.formatting import format_integer, format_number, format_percent
from reports.models import ReportState

logger = logging.getLogger(__name__)

TEMPLATE_DIRECTORY = Path(__file__).with_name("templates")
TEMPLATE_NAME = "executive_report.html"

REPORT_OBJECT_PREFIX = "reports/executive"


@lru_cache(maxsize=1)
def _get_template_environment() -> Environment:
    """Create and cache the Jinja report environment."""
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIRECTORY),
        autoescape=select_autoescape(
            enabled_extensions=("html",),
            default_for_string=True,
        ),
        undefined=StrictUndefined,
    )

    environment.filters["number"] = format_number
    environment.filters["integer"] = format_integer
    environment.filters["percent"] = format_percent

    return environment


def _get_minio_client() -> Minio:
    """Create the MinIO client used for report publishing."""
    settings = get_minio_settings()

    endpoint = settings.endpoint

    if "://" not in endpoint:
        endpoint = f"http://{endpoint}"

    parsed = urlparse(endpoint)

    if not parsed.netloc:
        raise ValueError(f"Invalid MINIO_ENDPOINT: {endpoint}")

    return Minio(
        endpoint=parsed.netloc,
        access_key=settings.user,
        secret_key=settings.password,
        secure=parsed.scheme == "https",
    )


def render_html(state: ReportState) -> dict[str, str]:
    """Render the report as a self-contained HTML document."""
    logger.info(f"Rendering executive report for {state['report_date']}")

    template = _get_template_environment().get_template(TEMPLATE_NAME)
    html = template.render(
        report_date=state["report_date"],
        metrics=state["metrics"],
        top_farms=state["top_farms"],
        narrative=state["narrative"],
        insights=state["insights"],
    )

    return {"html": html}


def publish_report(state: ReportState) -> dict[str, str]:
    """Publish the rendered report to the staging bucket."""
    settings = get_minio_settings()

    object_key = f"{REPORT_OBJECT_PREFIX}/date={state['report_date']}/report.html"

    content = state["html"].encode("utf-8")

    client = _get_minio_client()

    if not client.bucket_exists(settings.staging_bucket):
        raise RuntimeError(
            f"MinIO staging bucket does not exist: {settings.staging_bucket}"
        )

    client.put_object(
        bucket_name=settings.staging_bucket,
        object_name=object_key,
        data=io.BytesIO(content),
        length=len(content),
        content_type="text/html; charset=utf-8",
    )

    logger.info(
        f"Published executive report to s3://{settings.staging_bucket}/{object_key}"
    )

    return {
        "published_bucket": settings.staging_bucket,
        "object_key": object_key,
    }
