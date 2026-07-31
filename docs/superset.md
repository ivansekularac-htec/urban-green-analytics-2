# Superset Bootstrap Guide

This project bootstraps Apache Superset automatically during Docker startup. The initialization imports the complete BI environment, including:

* Database connection
* Datasets
* Dashboards
* Roles
* Row Level Security (RLS) policies

The only file that needs to be maintained is the exported Superset archive.

---

# Updating dashboards

Whenever dashboards, charts, or datasets are modified in Superset, a new export should be committed so that everyone receives the latest BI configuration after starting Docker.

## Step 1 — Export assets from Superset

Connect to the running Superset container:

```bash
docker exec -it urbangreen-superset bash
```

Export all dashboards and their dependencies to a ZIP archive:

```bash
superset export-dashboards -f /tmp/<file-name>.zip
```

The export is written to `/tmp` inside the container.

> **Note**
>
> Superset intentionally omits database passwords from exported database connections for security reasons.
>
> During project initialization, the bootstrap process automatically injects the configured ClickHouse database password into the export before importing it, so no manual changes to the ZIP archive are required.


---

# Step 2 — Copy the export from Docker

Copy file to your local repository:

```bash
docker cp urbangreen-superset:/tmp/<export-file>.zip \
infra/superset/exports/dashboards_export.zip
```

Replace `urbangreen-superset` with your container name if different.

The exported archive should always be committed as:

```text
infra/
└── superset/
    └── exports/
        └── dashboards_export.zip
```

---

# Step 3 — Commit the updated archive

Commit the new `dashboards_export.zip` together with any dashboard changes.

Anyone pulling the latest changes only needs to perform a fresh Docker startup:

```bash
docker compose down -v
docker compose up --build
```

The initialization will automatically import the updated BI assets.

---

# Row Level Security requirements

This project secures dashboard data using Superset Row Level Security (RLS).

The RLS policy filters data according to the currently logged-in user and the farm assignments stored in ClickHouse.

Because of this:

> **Every dataset protected by RLS must expose the `farm_id` column.**

Even if a chart never displays or groups by `farm_id`, the column **must still be present** in the dataset so the RLS filter can be evaluated.

For example, this is valid:

| column        |
| ------------- |
| metric_date   |
| total_yield   |
| premium_share |
| farm_id       |

The `farm_id` column does not need to be used by any visualization.

---

# How RLS works

The RLS policy compares the authenticated Superset user's email with the mirrored warehouse tables.

Internally the policy performs a lookup similar to:

```
Superset user email
        │
        ▼
dim_user
        │
        ▼
dim_user_farm_role
        │
        ▼
Allowed farm_ids
```

Only rows belonging to those farms are returned to the dashboard.

User-to-farm assignments originate in PostgreSQL and are mirrored into ClickHouse by the ETL pipeline.

---

# Bootstrap process

During Docker initialization the following steps are executed automatically:

1. Start Superset.
2. Import the exported Superset assets.
3. Inject the ClickHouse database password into the imported database connection.
4. Create demo roles and users.
5. Create Row Level Security policies.
6. Attach the RLS policy to every configured dataset.

After initialization, the entire BI environment is ready without any manual configuration.

---

# Troubleshooting

## Database connection fails after import

Database passwords are not stored inside Superset exports.

If the connection cannot be established, verify that the bootstrap script successfully injected the ClickHouse password before import.

---

## Dashboard shows data from every farm

Verify that:

* the dataset contains a `farm_id` column,
* the dataset has the RLS policy attached,
* the current user has farm assignments,
* `dim_user` and `dim_user_farm_role` have been populated by the ETL.

---

## Changes do not appear

Superset only imports the archive during initialization.

After replacing `dashboards_export.zip`, recreate the environment:

```bash
docker compose down -v
docker compose up --build
```

Alternatively, manually rerun the initialization script inside the Superset container.
