"""Helper functions for the API application."""

import time


def get_current_timestamp() -> int:
    return int(time.time())
