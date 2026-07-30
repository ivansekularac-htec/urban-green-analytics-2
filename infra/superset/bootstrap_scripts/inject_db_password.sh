#!/bin/sh

set -eu

TEMP_DIR=$(mktemp -d)

unzip -q /app/dashboards_export.zip -d "${TEMP_DIR}"

sed -i \
    "s/urbangreen:XXXXXXXXXX@/urbangreen:${CLICKHOUSE_PASSWORD}@/" \
    "${TEMP_DIR}/dashboard_export_20260730T161903/databases/ClickHouse_Connect_Superset.yaml"

cd "${TEMP_DIR}"

zip -qr /app/dashboards_export.zip .

cd -

rm -rf "${TEMP_DIR}"

echo "Password successfully injected"