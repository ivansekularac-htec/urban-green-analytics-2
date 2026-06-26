"""Registry of the ``app.*`` tables to extract.

Add or remove a table here and the DAG factory in ``extract_app_tables.py``
builds (or drops) its DAG automatically — no per-table code to duplicate.

Fields:
    name             table name in the ``app`` schema
    schedule         Airflow schedule (``@daily`` for most, ``@hourly`` for harvests)
    partition_by     optional column whose date partitions the output on disk
    partition_label  optional on-disk partition folder label (e.g. ``harvest_date``)
"""

DAILY = "@daily"
HOURLY = "@hourly"

TABLES: list[dict] = [
    {"name": "roles", "schedule": DAILY},
    {"name": "quality_grades", "schedule": DAILY},
    {"name": "farm_infrastructure_types", "schedule": DAILY},
    {"name": "growing_system_types", "schedule": DAILY},
    {"name": "crop_categories", "schedule": DAILY},
    {"name": "sensor_types", "schedule": DAILY},
    {"name": "farms", "schedule": DAILY},
    {"name": "users", "schedule": DAILY},
    {"name": "crops", "schedule": DAILY},
    {"name": "user_roles", "schedule": DAILY},
    {"name": "farm_crops", "schedule": DAILY},
    {"name": "sensors", "schedule": DAILY},
    {
        "name": "harvests",
        "schedule": HOURLY,
        "partition_by": "created_at",
        "partition_label": "harvest_date",
    },
]
