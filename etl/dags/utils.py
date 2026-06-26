from config import TABLES


def get_tables_by_schedule(schedule: str):
    return [t for t in TABLES if t["schedule"] == schedule]
