"""Build temporal join predicates for matching SCD2 dimension versions."""

from pyspark.sql import Column


def temporal_condition(
    event_key: Column,
    dimension_key: Column,
    event_timestamp: Column,
    valid_from: Column,
    valid_to: Column,
) -> Column:
    """
    Match an event to the dimension version valid at event time.

    Dimension validity follows the half-open interval:
    valid_from <= event_timestamp < valid_to
    """
    return (
        (event_key == dimension_key)
        & (event_timestamp >= valid_from)
        & (event_timestamp < valid_to)
    )
