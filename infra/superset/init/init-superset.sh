#!/bin/sh

set -eu

readonly SENTINEL_FILE="/app/superset_home/.initialized"
readonly ASSETS_SENTINEL_FILE="/app/superset_home/.assets-imported"

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

    touch "${SENTINEL_FILE}"

    echo "Superset initialization completed."
fi

echo "Seeding Superset users and business roles..."

python /scripts/seed_users_roles.py

if [ -f "${ASSETS_SENTINEL_FILE}" ]; then
    echo "Superset dashboard assets already imported. Skipping import."
else
    echo "Importing Superset dashboard assets..."

    python /assets/import.py

    touch "${ASSETS_SENTINEL_FILE}"

    echo "Superset dashboard assets imported successfully."
fi

echo "Seeding dashboard access..."

python /scripts/seed_dashboard_access.py

echo "Seeding farm-level row security..."

python /scripts/seed_rls.py

echo "Starting Superset..."

exec /usr/bin/run-server.sh
