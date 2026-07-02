"""Per-table extract cursor and pending watermark, stored as Airflow Variables."""

from airflow.sdk import Variable

DEFAULT_CURSOR = 0


def cursor_key(table):
    """Name of the Variable that holds the saved cursor for a table."""
    return f"extract_cursor_{table}"


def pending_key(table):
    """Name of the Variable that holds the frozen watermark during a run."""
    return f"extract_pending_{table}"


def get_cursor(table):
    """Read the saved cursor for a table, or the default when none exists yet."""
    return Variable.get(
        cursor_key(table), default=DEFAULT_CURSOR, deserialize_json=True
    )


def set_cursor(table, cursor):
    """Save the cursor for a table (call only after all writes succeed)."""
    Variable.set(cursor_key(table), cursor, serialize_json=True)


def set_pending(table, high):
    """Freeze this run's upper watermark before writing, so a retry reuses it."""
    Variable.set(pending_key(table), high, serialize_json=True)


def read_frozen_high(table, low):
    """Return a still-valid frozen watermark from a crashed run, else None."""
    high = Variable.get(pending_key(table), default=None, deserialize_json=True)
    if high is None:
        return None
    if int(high) <= int(low):
        return None
    return high


def clear_pending(table):
    """Remove the frozen watermark after the cursor has been advanced."""
    Variable.delete(pending_key(table))
