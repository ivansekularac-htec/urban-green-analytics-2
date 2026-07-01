# Airflow Extract Setup

This document explains how the Postgres extract surface works in the project and how the tagged files interact.
It is written for a developer who is new to Airflow.

## Overview

The Airflow extract surface lives in two places:

- `etl/dags/postgres_extract` - code that defines the extract and write logic
- `docs/airflow-setup.md` - documentation and explanation of that logic

The goal of this Airflow layer is to:

- extract only changed rows from every `app.*` table
- land those results in MinIO as Parquet
- keep a simple per-table DAG surface
- make cursor state visible and editable in Airflow UI
- preserve correctness for first-run backfills and retries

---

## Files and purpose

### `etl/dags/postgres_extract/tables.yaml`

This file lists the tables that the system extracts and their schedules.
Each entry contains:

- `name`: the table name in the `app` schema
- `schedule`: Airflow schedule string such as `@daily` or `@hourly`
- optional `partition_by` and `partition_label` for partitioned tables

Example:

```yaml
tables:
  - name: harvests
    schedule: "@hourly"
    partition_by: created_at
    partition_label: harvest_date
```

This file is the single source of truth for the extract surface.
If a new table should be extracted, add it here. If a table should be removed, delete it here.

### `etl/dags/dag_factory.py`

This module generates Airflow DAGs dynamically.
Instead of writing one DAG per table, it reads `tables.yaml` and creates one DAG for each entry.
That means the extract surface is configurable, not hard-coded.

Key behavior:

- load table configs from `tables.yaml`
- for each config, create a DAG with `dag_id` = `postgres_extract__{table}`
- each DAG contains one task: `run()`
- `run()` performs extraction, writes Parquet files, and advances the cursor

Inside `run()`:

1. read the last cursor from Airflow Variables
2. compute `cursor_from` for the output object key
3. call `extract_table(table)`
4. compute `cursor_to` from the returned watermark
5. call `write_table(...)`
6. write the successful cursor back to Airflow Variables
7. clear the pending watermark

This design keeps the DAG layer very small and lets the business logic live in `extract.py`, `write.py`, and `cursor.py`.

### `etl/dags/postgres_extract/cursor.py`

This file manages incremental state.
It is responsible for reading and writing the cursor and the pending high watermark.

Important functions:

- `_cursor_key(table)`: returns Airflow Variable name for the table cursor
- `_high_watermark_key(table)`: returns Airflow Variable name for the pending watermark
- `get_cursor(table)`: reads the last successful cursor
- `set_cursor(table, cursor)`: writes the successful cursor
- `set_pending_high_watermark(table, watermark)`: writes a temporary watermark before file write
- `clear_pending_high_watermark(table)`: deletes the temporary watermark after success
- `_run_cutoff(pg)`: calculates the current epoch second as the read upper bound
- `_high_watermark(pg, table, low, run_cutoff)`: finds the newest `(updated_at, id)` in the allowed window

Why this matters:

- `get_cursor()` tells the extractor where the previous successful run stopped
- `set_pending_high_watermark()` prevents the cursor from advancing before the file is written
- `clear_pending_high_watermark()` makes retries safe
- `_high_watermark()` makes sure only rows up to the current run are included

### `etl/dags/postgres_extract/extract.py`

This file performs the actual Postgres extraction.
It contains a couple of helper functions and one main function: `extract_table(table)`.

Key functions:

- `_select_query(table, has_cursor)`: returns the SQL query for either initial or incremental extraction
- `_build_query_parameters(current_cursor, run_cutoff)`: builds the query arguments
- `_fetch_rows(cursor, table)`: reads rows from the DB, using chunked fetch for harvests
- `extract_table(table)`: orchestrates the whole extraction

Detailed behavior of `extract_table(table)`:

1. read the current cursor using `get_cursor(table)`
2. determine whether a cursor exists
3. create a Postgres hook using `PostgresHook`
4. calculate `run_cutoff` with `_run_cutoff(hook)`
5. compute the next watermark with `_high_watermark(...)`
6. if no watermark is found, raise `AirflowSkipException`
7. set the pending watermark so the run can be tracked
8. execute the select query
9. read the column names from `cursor.description`
10. read rows using `_fetch_rows(...)`
11. if no rows are returned, clear the pending watermark and raise `AirflowSkipException`
12. return `(columns, rows, high_watermark)`

Why this is important:

- first run performs a full backfill up to `run_cutoff`
- subsequent runs only read changes since the last cursor
- `harvests` is read in chunks to avoid loading too much data
- the cursor only advances after the extraction and write succeed

### `etl/dags/postgres_extract/write.py`

This file writes the extracted rows to MinIO as Parquet.
It is responsible for constructing deterministic object keys and uploading files.

Key functions:

- `_write_parquet_to_minio(df, key)`: writes a local Parquet file and uploads it to MinIO
- `_build_object_key(...)`: builds the S3-style object key for a file
- `write_table(...)`: converts rows into a DataFrame and writes one or more Parquet files

What `write_table()` does:

1. create a `DataFrame` from the extracted rows and columns
2. if the table is `harvests` and partitioning is enabled:
   - convert `created_at` timestamp seconds into a date
   - group rows by `harvest_date`
   - write each date group into its own Parquet file
3. otherwise, write one Parquet file for the full result set
4. return the list of MinIO object keys that were written

How object keys are formed:

- base prefix is `app/raw/postgres`
- the key includes table name, cursor range, and optional partition info
- example:
  `app/raw/postgres/harvests/updated_at_from=0/updated_at_to=1700000000/harvest_date=2026-06-30/part-00001.parquet`

Why this is useful:

- operators can see the source table and the time range in the key
- files are easy to identify and recover
- ordered, deterministic keys help with debugging and downstream processing

---

## How the pieces fit together

For each table run, the flow is:

1. Airflow starts the DAG `postgres_extract__{table}`
2. the DAG task reads the previous cursor
3. the extractor computes the next watermark and reads changed rows
4. the pending watermark gets stored before write
5. the writer writes Parquet files to MinIO
6. the successful cursor gets stored
7. the pending watermark is cleared

This is the simplest correct pattern for incremental extract:
- do not advance the cursor until write succeeds
- keep the cursor editable in Airflow UI
- support backfill on first run
- read only changed rows on repeat runs

---

## Airflow-specific concepts

### DAG

A DAG is not a job itself. It is a definition of a workflow.
`dag_factory.py` produces DAGs, and Airflow schedules them.

### Task

A task is a step within a DAG. In this implementation, each DAG has one task called `run()`.
That task performs extraction, writing, and cursor advancement.

### Airflow Variables

Variables in Airflow are key/value pairs stored in metadata.
This project uses them for state:

- `extract_cursor__{table}` - last successful extraction point
- `extract_high_watermark__{table}` - pending watermark during a running extraction

These are visible and editable in the UI.

### AirflowSkipException

When no new rows are available, the extractor raises `AirflowSkipException`.
Airflow marks the task as skipped rather than failed.
That is the correct behavior for an incremental extraction with no new data.

---

## Practical notes for running the stack

### What to check first

- `urbangreen_db` connection exists in Airflow
- `urbangreen_minio` connection exists in Airflow
- MinIO bucket `staging` exists
- DAGs appear in Airflow UI as `postgres_extract__...`
- the schedule in `tables.yaml` is applied correctly

### How to inspect state

In Airflow UI:

- go to `Admin > Variables`
- look for `extract_cursor__{table}` and `extract_high_watermark__{table}`
- inspect the `Task Instance` logs for a DAG run
- verify whether the task was `success` or `skipped`

### What `skipped` means

A skipped run means:
- there were no new rows in the selected table range
- or the watermark query found nothing to process

This is expected for incremental extraction.

---

## Why this design matters

This implementation is intentionally simple and safe:

- `tables.yaml` is the only place you change the extract surface
- the DAG layer is minimal and repeatable
- cursor state is externalized to Airflow Variables
- the writer produces deterministic object keys
- harvests is handled with chunked reading and partitioned output
