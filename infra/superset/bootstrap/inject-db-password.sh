#!/bin/sh

set -eu

SOURCE_ZIP="/app/dashboards_export.zip"
PATCHED_ZIP="/tmp/dashboards_export.zip"

TEMP_DIR=$(mktemp -d)

echo "Extracting Superset export..." >&2

unzip -q "${SOURCE_ZIP}" -d "${TEMP_DIR}"

echo "Injecting ClickHouse password..." >&2

sed -i \
    "s/urbangreen:XXXXXXXXXX@/urbangreen:${CLICKHOUSE_PASSWORD}@/" \
    "${TEMP_DIR}"/dashboard_export_*/databases/ClickHouse_Connect_Superset.yaml

echo "Creating patched export..." >&2

cd "${TEMP_DIR}"

zip -qr "${PATCHED_ZIP}" .

cd - >/dev/null

rm -rf "${TEMP_DIR}"

echo "${PATCHED_ZIP}"