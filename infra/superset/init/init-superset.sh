#!/bin/sh
set -eu

SUPERSET_HOME="${SUPERSET_HOME:-/app/superset_home}"
SENTINEL_FILE="${SUPERSET_HOME}/.urbangreen-superset-initialized"

: "${SUPERSET_SECRET_KEY:?SUPERSET_SECRET_KEY is required}"

mkdir -p "${SUPERSET_HOME}"

if [ -f "${SENTINEL_FILE}" ]; then
    echo "[superset-init] Sentinel found. Skipping metadata bootstrap and admin creation."
else
    : "${SUPERSET_ADMIN_USERNAME:?SUPERSET_ADMIN_USERNAME is required}"
    : "${SUPERSET_ADMIN_PASSWORD:?SUPERSET_ADMIN_PASSWORD is required}"
    : "${SUPERSET_ADMIN_FIRSTNAME:?SUPERSET_ADMIN_FIRSTNAME is required}"
    : "${SUPERSET_ADMIN_LASTNAME:?SUPERSET_ADMIN_LASTNAME is required}"
    : "${SUPERSET_ADMIN_EMAIL:?SUPERSET_ADMIN_EMAIL is required}"

    report_bootstrap_failure() {
        exit_code=$?
        trap - EXIT

        if [ "${exit_code}" -ne 0 ]; then
            echo "[superset-init] Bootstrap failed with exit code ${exit_code}."
            echo "[superset-init] Metadata was preserved and the sentinel was not created."
        fi

        exit "${exit_code}"
    }

    trap report_bootstrap_failure EXIT

    echo "[superset-init] Sentinel not found. Starting bootstrap."

    echo "[superset-init] Step 1/3: Applying metadata database migrations."
    superset db upgrade

    echo "[superset-init] Step 2/3: Creating admin user '${SUPERSET_ADMIN_USERNAME}'."
    superset fab create-admin \
        --username "${SUPERSET_ADMIN_USERNAME}" \
        --password "${SUPERSET_ADMIN_PASSWORD}" \
        --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
        --lastname "${SUPERSET_ADMIN_LASTNAME}" \
        --email "${SUPERSET_ADMIN_EMAIL}"

    echo "[superset-init] Step 3/3: Initializing roles and permissions."
    superset init

    touch "${SENTINEL_FILE}"
    trap - EXIT

    echo "[superset-init] Bootstrap completed successfully. Sentinel created."
fi

echo "[superset-init] Starting Superset web server."

exec gunicorn \
    --bind "0.0.0.0:${SUPERSET_PORT:-8088}" \
    --workers 1 \
    --worker-class gthread \
    --threads 20 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    "superset.app:create_app()"
    