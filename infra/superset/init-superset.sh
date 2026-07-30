#!/bin/sh

set -eu

# # Admin user
# SUPERSET_ADMIN_USERNAME="${SUPERSET_ADMIN_USERNAME:-admin}"
# SUPERSET_ADMIN_FIRSTNAME="${SUPERSET_ADMIN_FIRSTNAME:-Admin}"
# SUPERSET_ADMIN_LASTNAME="${SUPERSET_ADMIN_LASTNAME:-User}"
# SUPERSET_ADMIN_EMAIL="${SUPERSET_ADMIN_EMAIL:-admin@urbangreen.com}"
# SUPERSET_ADMIN_PASSWORD="${SUPERSET_ADMIN_PASSWORD}"

# # Farm Manager demo user
# DEMO_FARM_MANAGER_USERNAME="${DEMO_FARM_MANAGER_USERNAME:-fm1}"
# DEMO_FARM_MANAGER_FIRSTNAME="${DEMO_FARM_MANAGER_FIRSTNAME:-Farm}"
# DEMO_FARM_MANAGER_LASTNAME="${DEMO_FARM_MANAGER_LASTNAME:-Manager}"
# DEMO_FARM_MANAGER_EMAIL="${DEMO_FARM_MANAGER_EMAIL:-fm1@urbangreen.com}"
# DEMO_FARM_MANAGER_PASSWORD="${DEMO_FARM_MANAGER_PASSWORD}"

# # Operations Team demo user
# DEMO_OPERATIONS_USERNAME="${DEMO_OPERATIONS_USERNAME:-ot1}"
# DEMO_OPERATIONS_FIRSTNAME="${DEMO_OPERATIONS_FIRSTNAME:-Operations}"
# DEMO_OPERATIONS_LASTNAME="${DEMO_OPERATIONS_LASTNAME:-Team}"
# DEMO_OPERATIONS_EMAIL="${DEMO_OPERATIONS_EMAIL:-ot1@urbangreen.com}"
# DEMO_OPERATIONS_PASSWORD="${DEMO_OPERATIONS_PASSWORD}"

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

    /app/create_users.sh

    echo "Injecting ClickHouse password..."

    /app/inject_db_password.sh

    echo "Importing dashboards and datasets..."

    superset import-dashboards \
        --path /app/dashboards_export.zip \
        -u "${SUPERSET_ADMIN_USERNAME}"

    echo "Creating Row Level Security rules..."

    python /app/create_rls.py

    touch "${SENTINEL_FILE}"

    echo "Superset initialization completed."
fi

echo "Starting Superset..."

exec /usr/bin/run-server.sh

