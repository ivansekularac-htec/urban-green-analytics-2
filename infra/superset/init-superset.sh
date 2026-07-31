#!/bin/sh

set -eu

readonly SENTINEL_FILE="/app/superset_home/.initialized"

if [ -f "${SENTINEL_FILE}" ]; then
    echo "Superset already initialized. Skipping bootstrap."
else
    echo "Initializing Superset metadata database..."

    superset db upgrade

    echo "Initializing Superset application..."

    superset init

    echo "Importing roles..."

    superset fab import-roles \
        --path /app/roles.json

    echo "Creating users..."

    /app/bootstrap/create-users.sh

    echo "Importing dashboards and datasets..."

    python /app/bootstrap/import_dashboards.py

    echo "Creating Row Level Security rules..."

    python /app/bootstrap/create_rls.py

    touch "${SENTINEL_FILE}"

    echo "Superset initialization completed."
fi

echo "Starting Superset..."

exec /usr/bin/run-server.sh

