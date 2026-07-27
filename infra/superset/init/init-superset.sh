#!/bin/bash
set -eu

# Marker file used to detect whether Superset has already been initialized.
# It prevents migrations, admin creation, and permission setup from running
# every time the container starts.
SENTINEL="/app/superset_home/.initialized"

# Perform one-time initialization on the first container startup.
if [ ! -f "$SENTINEL" ]; then
    echo "[INIT] First Superset startup"
    echo "[INIT] Running database migrations"

    # Create or upgrade the Superset metadata database schema.
    superset db upgrade

    echo "[INIT] Creating admin user"

    # Create the initial administrator account.
    superset fab create-admin \
        --username "${SUPERSET_ADMIN_USERNAME}" \
        --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
        --lastname "${SUPERSET_ADMIN_LASTNAME}" \
        --email "${SUPERSET_ADMIN_EMAIL}" \
        --password "${SUPERSET_ADMIN_PASSWORD}"

    echo "[INIT] Initializing Superset permissions"

    # Initialize default roles, permissions, and security metadata.
    superset init

    echo "[INIT] Bootstrap completed"

    # Mark initialization as completed.
    touch "$SENTINEL"

else
    echo "[INIT] Existing Superset installation detected"
    echo "[INIT] Skipping bootstrap"
fi

echo "[INIT] Starting Superset server"

# Replace the shell process with the Gunicorn server.
exec gunicorn \
    --bind 0.0.0.0:8088 \
    --workers 1 \
    "superset.app:create_app()"