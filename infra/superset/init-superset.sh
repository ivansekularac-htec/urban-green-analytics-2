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
        --lastname "${SUPERSET_ADMIN_LASTNAME:-User}" \
        --email "${SUPERSET_ADMIN_EMAIL:-admin@urbangreen.com}" \
        --password "${SUPERSET_ADMIN_PASSWORD}"

    echo "Initializing Superset roles and permissions..."

    superset init

    touch "${SENTINEL_FILE}"

    echo "Superset initialization completed."
fi

echo "Starting Superset..."
exec /usr/bin/run-server.sh
