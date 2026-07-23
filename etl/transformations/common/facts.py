"""Helpers shared by the fact loaders.

The difference between a fact and a Type 2 dimension row is that a fact happens
at one fixed instant and never changes afterwards. That is what makes it safe
to freeze a dimension surrogate into it: the loader resolves which version was
valid at that instant, writes that surrogate, and a later change to the
dimension leaves the fact untouched. A report over a past period therefore
keeps showing the attributes as they were then.
"""

import logging

from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def date_key(column):
    """Warehouse date key as YYYYMMDD, matching dim_date."""
    return F.date_format(F.col(column), "yyyyMMdd").cast("int")


def time_key(column):
    """Warehouse time key at minute grain: hour * 100 + minute, matching dim_time."""
    return (F.hour(F.col(column)) * 100 + F.minute(F.col(column))).cast("int")


def as_of_version(facts, dim, natural_key, event_ts, attributes):
    """Attach attributes of the dimension version valid at event time.

    The join carries the half-open interval condition the SCD2 tables are built
    for, so exactly one version matches any instant.

    The join is a left join: a fact whose dimension row has not been loaded yet
    must not disappear. Losing a harvest because its farm is missing would
    understate every total that reads the fact, and the loss would be silent.
    Such rows keep the fallback value and can be repaired by a later run.
    """
    dim_alias = "d"
    matched = facts.alias("f").join(
        dim.alias(dim_alias),
        (F.col(f"f.{natural_key}") == F.col(f"{dim_alias}.{natural_key}"))
        & (F.col(f"f.{event_ts}") >= F.col(f"{dim_alias}.valid_from"))
        & (F.col(f"f.{event_ts}") < F.col(f"{dim_alias}.valid_to")),
        "left",
    )

    selected = [F.col(f"f.{c}").alias(c) for c in facts.columns]
    selected += [
        F.coalesce(F.col(f"{dim_alias}.{source}"), F.lit(fallback)).alias(alias)
        for source, alias, fallback in attributes
    ]
    return matched.select(selected)
