#!/bin/sh

set -eu

echo "Running Superset database migrations..."
superset db upgrade

echo "Ensuring Admin user exists..."
python -m bootstrap.bootstrap_security --ensure-admin-only

echo "Initializing Superset roles and permissions..."
superset init

echo "Running full Superset security + content bootstrap..."
python -m bootstrap.bootstrap_security

echo "Starting Superset..."
exec /usr/bin/run-server.sh
