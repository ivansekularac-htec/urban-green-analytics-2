-- ============================================================
-- Sensors
-- 1 sensor of each sensor_type is created for each farm
-- ============================================================

INSERT INTO urbangreen.sensors (
    farm_id,
    sensor_type_id,
    serial_number,
    status,
    installed_at
)
SELECT
    f.farm_id,
    st.sensor_type_id,
    CONCAT(
        CASE st.name
            WHEN 'Temperature' THEN 'TEMP-'
            WHEN 'Humidity' THEN 'HUM-'
            WHEN 'Light Intensity' THEN 'LIGHT-'
            WHEN 'pH Level' THEN 'PH-'
            WHEN 'Energy Usage' THEN 'ENER-'
            WHEN 'CO2 Concentration' THEN 'CO2-'
            ELSE 'SENSOR-'
        END,
        LPAD(f.farm_id::TEXT, 4, '0'),
        '-',
        LPAD(st.sensor_type_id::TEXT, 4, '0')
    ) AS serial_number,
    'ACTIVE'::urbangreen.sensor_status AS status,
    EXTRACT(EPOCH FROM NOW())::BIGINT AS installed_at
FROM urbangreen.farms f
CROSS JOIN urbangreen.sensor_types st;


-- ============================================================
-- Farm crops
-- Assigned all crops to all farms.
-- ============================================================

INSERT INTO urbangreen.farm_crops (
    farm_id,
    crop_id,
    started_at,
    ended_at
)
SELECT
    f.farm_id,
    c.crop_id,
    EXTRACT(EPOCH FROM NOW())::BIGINT AS started_at,
    NULL AS ended_at
FROM urbangreen.farms f
CROSS JOIN urbangreen.crops c;