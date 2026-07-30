#!/bin/sh

set -eu


echo "Creating Superset admin user..."

superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME}" \
    --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
    --lastname "${SUPERSET_ADMIN_LASTNAME}" \
    --email "${SUPERSET_ADMIN_EMAIL}" \
    --password "${SUPERSET_ADMIN_PASSWORD}"


echo "Creating Farm Manager user..."

superset fab create-user \
    --username "${DEMO_FARM_MANAGER_USERNAME}" \
    --firstname "${DEMO_FARM_MANAGER_FIRSTNAME}" \
    --lastname "${DEMO_FARM_MANAGER_LASTNAME}" \
    --email "${DEMO_FARM_MANAGER_EMAIL}" \
    --password "${DEMO_FARM_MANAGER_PASSWORD}" \
    --role FarmManager


echo "Creating Operations Team user..."

superset fab create-user \
    --username "${DEMO_OPERATIONS_USERNAME}" \
    --firstname "${DEMO_OPERATIONS_FIRSTNAME}" \
    --lastname "${DEMO_OPERATIONS_LASTNAME}" \
    --email "${DEMO_OPERATIONS_EMAIL}" \
    --password "${DEMO_OPERATIONS_PASSWORD}" \
    --role OperationsTeam


echo "User creation completed."