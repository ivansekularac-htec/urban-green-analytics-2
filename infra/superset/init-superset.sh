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

    echo "Initializing Superset roles and permissions..."

    superset init

    echo "Importing roles..."

    superset fab import-roles --path /app/roles.json

    echo "Creating demo users..."

    superset fab create-user \
        --username fm1 \
        --firstname Farm \
        --lastname Manager \
        --email fm1.@urbangreen.com \
        --password "${SUPERSET_FARM_MANAGER_PASSWORD:-fm1}" \
        --role FarmManager

    superset fab create-user \
        --username ot1 \
        --firstname Operations \
        --lastname Team \
        --email ot1@urbangreen.com \
        --password "${SUPERSET_OPERATIONS_PASSWORD:-ot1}" \
        --role OperationsTeam

    # echo "Creating demo roles and users..."

    # python /app/create_roles_users.py

    touch "${SENTINEL_FILE}"

    echo "Superset initialization completed."
fi

echo "Starting Superset..."
exec /usr/bin/run-server.sh
