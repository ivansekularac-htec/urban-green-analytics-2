CREATE SCHEMA IF NOT EXISTS app;
SET search_path TO app;

-- Mark selected sensors as OFFLINE.
-- Keep this list in sync with DISABLED_SENSOR_IDS in the simulator so the
-- same sensors are marked as offline in Postgres and emit no readings.
UPDATE sensors
SET status = 'OFFLINE'
WHERE id IN (
    5, 17, 42, 89, 113, 156, 201, 278, 344, 417
);