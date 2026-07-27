#!/bin/sh
set -eu

SUPERSET_HOME="${SUPERSET_HOME:-/app/superset_home}"
SENTINEL="${SUPERSET_HOME}/.bootstrapped"

mkdir -p "${SUPERSET_HOME}"

echo "Applying DB migrations..."
superset db upgrade

if [ ! -f "${SENTINEL}" ]; then
  echo "First boot: seeding admin and roles..."

  echo "Creating admin user..."
  superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME}" \
    --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
    --lastname "${SUPERSET_ADMIN_LASTNAME}" \
    --email "${SUPERSET_ADMIN_EMAIL}" \
    --password "${SUPERSET_ADMIN_PASSWORD}"

  echo "Setting up roles and permissions..."
  superset init

  touch "${SENTINEL}"
  echo "Bootstrap complete; sentinel written to ${SENTINEL}"
else
  echo "Sentinel ${SENTINEL} found; skipping admin setup and init"
fi

exec /usr/bin/run-server.sh