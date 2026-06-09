INSERT INTO urbangreen.sensors (farm_id, sensor_type_id, serial_number, status)
SELECT
  f.id AS farm_id,
  s.id AS sensor_type_id,
  CONCAT(
    CASE s.id
      WHEN 1 THEN 'TEMP-20240315-'
      WHEN 2 THEN 'HUM-20240322-'
      WHEN 3 THEN 'LIGHT-20240320-'
      WHEN 4 THEN 'PH-20240318-'
      WHEN 5 THEN 'ENER-20240325-'
      WHEN 6 THEN 'CO2-20240319-'
    END,
    lpad(((f.id - 1) * 6 + s.id)::text, 3, '0')
  ) AS serial_number,
  'ACTIVE'::urbangreen.sensor_status AS status
FROM generate_series(1, 75) AS f(id)
CROSS JOIN generate_series(1, 6) AS s(id);