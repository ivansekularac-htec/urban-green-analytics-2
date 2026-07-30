#!/bin/sh

set -eu

readonly SENTINEL_FILE="/app/superset_home/.initialized"

if [ -f "${SENTINEL_FILE}" ]; then
    echo "Superset already initialized. Skipping bootstrap."
else
    echo "Initializing Superset metadata database..."

    superset db upgrade

    echo "Creating admin user..."

    superset fab create-admin \
        --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
        --firstname "${SUPERSET_ADMIN_FIRSTNAME:-Admin}" \
        --lastname "${SUPERSET_ADMIN_LASTNAME:-Admin}" \
        --email "${SUPERSET_ADMIN_EMAIL:-admin@urbangreen.com}" \
        --password "${SUPERSET_ADMIN_PASSWORD}"

    echo "Init the Superset application..."

    superset init

    echo "Importing datasources (database connection and datasets)..."

    superset legacy-import-datasources --path /app/datasources.yaml

    echo "Importing roles..."

    superset fab import-roles --path /app/roles.json

    echo "Creating demo users..."

    superset fab create-user \
        --username "${SUPERSET_FARM_MANAGER_USERNAME:-fm1}" \
        --firstname "${SUPERSET_FARM_MANAGER_FIRSTNAME:-Farm}" \
        --lastname "${SUPERSET_FARM_MANAGER_LASTNAME:-Manager}" \
        --email "${SUPERSET_FARM_MANAGER_EMAIL:-fm1@urbangreen.com}" \
        --password "${SUPERSET_FARM_MANAGER_PASSWORD}" \
        --role FarmManager

    superset fab create-user \
        --username "${SUPERSET_FARM_MANAGER_USERNAME:-ot1}" \
        --firstname "${SUPERSET_FARM_MANAGER_FIRSTNAME:-Operations}" \
        --lastname "${SUPERSET_FARM_MANAGER_LASTNAME:-Team}" \
        --email "${SUPERSET_FARM_MANAGER_EMAIL:-ot1@urbangreen.com}" \
        --password "${SUPERSET_OPERATIONS_PASSWORD}" \
        --role OperationsTeam

    touch "${SENTINEL_FILE}"

    echo "Superset initialization completed."
fi

echo "Starting Superset..."
exec /usr/bin/run-server.sh
