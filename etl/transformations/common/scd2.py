"""Type 2 slowly changing dimension handling shared by the SCD2 loaders.

A Type 2 dimension keeps one row per version of an entity, valid in
[valid_from, valid_to). Facts join it with

    event_ts >= valid_from AND event_ts < valid_to

so a report over a past period shows the attributes as they were then.

Closing a version does not use ALTER TABLE UPDATE, which ClickHouse only
supports as an expensive asynchronous mutation. Every SCD2 table is a
ReplacingMergeTree whose sorting key ends with valid_from, so the open version
is closed by inserting the same row again - identical natural key and
valid_from - carrying valid_to, is_current = 0 and a higher _version. The merge
keeps the row with the highest _version, so the closed row wins. Everything is
an append, which also makes a re-run harmless: the same input produces the same
rows and collapses back to one.
"""

import logging
from datetime import datetime, timezone

from pyspark.sql import functions as F

from common import clickhouse

logger = logging.getLogger(__name__)

# Open-ended versions carry this instead of NULL, so the half-open interval
# check works without a special case for the current row.
FAR_FUTURE = "2099-12-31 23:59:59"

# The first version of an entity opens here rather than at the source
# timestamp. That timestamp says when the row was last written, not when the
# entity came into existence, so facts that predate the first warehouse load
# would fall outside every interval and join to nothing - silently losing their
# dimension attributes. Opening the initial version at the beginning of time
# attributes that earlier history to the first known state, which is the only
# state on record for it. Every later version still carries its real change
# timestamp, so history stays exact from the moment the warehouse began
# tracking it.
INITIAL_VALID_FROM = "1970-01-01 00:00:00"

CHANGE_HASH = "_change_hash"


def change_hash(columns):
    """Hash of the tracked attributes, used to detect a real change.

    Comparing one hash instead of every column keeps the join readable and
    keeps the tracked-attribute list in a single place. NULL is folded to an
    empty string so a value appearing or disappearing still changes the hash.
    """
    parts = [F.coalesce(F.col(c).cast("string"), F.lit("")) for c in columns]
    return F.sha2(F.concat_ws("||", *parts), 256)


def _load_version():
    """Load time in milliseconds, used as the ReplacingMergeTree version."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def apply_scd2(incoming, table, natural_key, tracked_columns, surrogate_column):
    """Close changed versions and open new ones for a Type 2 dimension.

    incoming carries the business columns plus valid_from, and holds exactly
    one row per natural key - the caller collapses the raw slices first.

    The surrogate column is left out of both writes. Its DDL default is a
    deterministic hash of the version identity, so ClickHouse recomputes the
    same value the previous load produced instead of the loader having to keep
    that expression in sync.
    """
    spark = incoming.sparkSession
    version = _load_version()

    current = clickhouse.read_query(
        spark, f"SELECT * FROM {table} FINAL WHERE is_current = 1"
    ).drop(surrogate_column, "_version")

    incoming = incoming.withColumn(CHANGE_HASH, change_hash(tracked_columns))
    current = current.withColumn(CHANGE_HASH, change_hash(tracked_columns))

    paired = incoming.alias("i").join(
        current.alias("c"),
        F.col(f"i.{natural_key}") == F.col(f"c.{natural_key}"),
        "left",
    )

    is_new = F.col(f"c.{natural_key}").isNull()
    is_changed = F.col(f"i.{CHANGE_HASH}") != F.col(f"c.{CHANGE_HASH}")

    # A source row older than the open version would rewrite history backwards,
    # which happens when an extract slice is replayed out of order.
    is_newer = F.col("i.valid_from") > F.col("c.valid_from")

    business_columns = [c for c in incoming.columns if c != CHANGE_HASH]

    def opened_column(column):
        """Take the incoming value, except for the initial version's bound."""
        if column == "valid_from":
            return (
                F.when(is_new, F.lit(INITIAL_VALID_FROM).cast("timestamp"))
                .otherwise(F.col("i.valid_from"))
                .alias("valid_from")
            )
        return F.col(f"i.{column}").alias(column)

    opened = (
        paired.filter(is_new | (is_changed & is_newer))
        .select([opened_column(c) for c in business_columns])
        .withColumn("valid_to", F.lit(FAR_FUTURE).cast("timestamp"))
        .withColumn("is_current", F.lit(1).cast("tinyint"))
        .withColumn("_version", F.lit(version).cast("long"))
    )

    closing_columns = [c for c in current.columns if c != CHANGE_HASH]

    closed = (
        paired.filter(is_changed & is_newer)
        .select(
            [F.col(f"c.{c}").alias(c) for c in closing_columns]
            + [F.col("i.valid_from").alias("_new_valid_from")]
        )
        .withColumn("valid_to", F.col("_new_valid_from"))
        .withColumn("is_current", F.lit(0).cast("tinyint"))
        .withColumn("_version", F.lit(version).cast("long"))
        .drop("_new_valid_from")
    )

    closed_count = clickhouse.write_table(closed, table) if not closed.isEmpty() else 0
    opened_count = clickhouse.write_table(opened, table) if not opened.isEmpty() else 0

    logger.info(f"{table}: opened {opened_count}, closed {closed_count}")
    return opened_count, closed_count
