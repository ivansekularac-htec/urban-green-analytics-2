SET session_replication_role = 'replica';

CREATE TEMP TABLE temp_roles (id BIGINT, name VARCHAR(50), description VARCHAR(255));
COPY temp_roles FROM '/var/lib/postgresql/data_import/roles.csv' DELIMITER ',' CSV HEADER;
INSERT INTO roles (id, name, description, created_at, updated_at)
SELECT id, name, description, 1717833600, 1717833600 FROM temp_roles;
DROP TABLE temp_roles;

CREATE TEMP TABLE temp_quality_grades (id BIGINT, name VARCHAR(50), description VARCHAR(255));
COPY temp_quality_grades FROM '/var/lib/postgresql/data_import/quality_grades.csv' DELIMITER ',' CSV HEADER; 

INSERT INTO quality_grades (id, code, name, description, created_at, updated_at)
SELECT 
  id, 
  UPPER(RIGHT(SPLIT_PART(name, ' - ', 1), 1)) AS code, 
  name, 
  description, 
  1717833600, 
  1717833600 
FROM temp_quality_grades;

DROP TABLE temp_quality_grades;

CREATE TEMP TABLE temp_infra (id BIGINT, name VARCHAR(50), description VARCHAR(255));
COPY temp_infra FROM '/var/lib/postgresql/data_import/infrastructure_types.csv' DELIMITER ',' CSV HEADER;
INSERT INTO farm_infrastructure_types (id, name, description, created_at, updated_at)
SELECT id, name, description, 1717833600, 1717833600 FROM temp_infra;

INSERT INTO farm_infrastructure_types (id, name, description, created_at, updated_at)
VALUES (3, 'Aeroponic', 'Aeroponic infrastructure facility', 1717833600, 1717833600);
DROP TABLE temp_infra;

CREATE TEMP TABLE temp_growing_systems (id BIGINT, name VARCHAR(50), description VARCHAR(255));
COPY temp_growing_systems FROM '/var/lib/postgresql/data_import/growing_system_types.csv' DELIMITER ',' CSV HEADER;
INSERT INTO growing_system_types (id, name, description, created_at, updated_at)
SELECT id, name, description, 1717833600, 1717833600 FROM temp_growing_systems;
DROP TABLE temp_growing_systems;

CREATE TEMP TABLE temp_crop_cats (id BIGINT, name VARCHAR(50), description VARCHAR(255));
COPY temp_crop_cats FROM '/var/lib/postgresql/data_import/crop_categories.csv' DELIMITER ',' CSV HEADER;
INSERT INTO crop_categories (id, name, description, created_at, updated_at)
SELECT id, name, description, 1717833600, 1717833600 FROM temp_crop_cats;
DROP TABLE temp_crop_cats;

CREATE TEMP TABLE temp_sensor_types (id BIGINT, name VARCHAR(50), unit VARCHAR(50), description VARCHAR(255), min_val DECIMAL, max_val DECIMAL);
COPY temp_sensor_types FROM '/var/lib/postgresql/data_import/sensor_types.csv' DELIMITER ',' CSV HEADER;
INSERT INTO sensor_types (id, name, unit, description, optimal_min, optimal_max, created_at, updated_at)
SELECT id, name, unit, description, min_val, max_val, 1717833600, 1717833600 FROM temp_sensor_types;
DROP TABLE temp_sensor_types;

CREATE TEMP TABLE temp_crops (id BIGINT, name VARCHAR(50), cat_name VARCHAR(50), description VARCHAR(255));
COPY temp_crops FROM '/var/lib/postgresql/data_import/crops.csv' DELIMITER ',' CSV HEADER;
INSERT INTO crops (id, category_id, name, description, created_at, updated_at)
SELECT tc.id, cc.id, tc.name, tc.description, 1717833600, 1717833600
FROM temp_crops tc
LEFT JOIN crop_categories cc ON tc.cat_name = cc.name;
DROP TABLE temp_crops;

CREATE TEMP TABLE temp_farms (id BIGINT, name VARCHAR(50), city VARCHAR(50), size_m2 DECIMAL, infra_name VARCHAR(50), system_name VARCHAR(50), beds INTEGER);
COPY temp_farms FROM '/var/lib/postgresql/data_import/farms.csv' DELIMITER ',' CSV HEADER;
INSERT INTO farms (id, infrastructure_type_id, growing_system_type_id, name, city, size_m2, status, growing_beds_count, created_at, updated_at)
SELECT 
    tf.id, 
    COALESCE(fit.id, 3),
    COALESCE(gst.id, 1),
    tf.name, tf.city, tf.size_m2, 'active'::farm_status, tf.beds, 1717833600, 1717833600
FROM temp_farms tf
LEFT JOIN farm_infrastructure_types fit ON tf.infra_name = fit.name
LEFT JOIN growing_system_types gst ON tf.system_name = gst.name;
DROP TABLE temp_farms;

CREATE SEQUENCE IF NOT EXISTS harvests_id_seq;
ALTER TABLE harvests ALTER COLUMN id SET DEFAULT nextval('harvests_id_seq');

COPY harvests (farm_id, crop_id, weight_kg, quality_grade_id, created_at, updated_at)
FROM PROGRAM 'gunzip -c /var/lib/postgresql/data_import/harvests.csv.gz'
WITH (FORMAT csv, HEADER true, NULL '');

SELECT setval('harvests_id_seq', (SELECT COALESCE(MAX(id), 1) FROM harvests));

CREATE SEQUENCE IF NOT EXISTS sensors_id_seq;
ALTER TABLE sensors ALTER COLUMN id SET DEFAULT nextval('sensors_id_seq');
INSERT INTO sensors (id, farm_id, sensor_type_id, serial_number, status, installed_at, created_at, updated_at)
SELECT

  ROW_NUMBER() OVER () AS id,
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
    LPAD(((f.id - 1) * 6 + s.id)::text, 3, '0')
  ) AS serial_number,
  'active'::sensor_status AS status,
  1717833600 AS installed_at,
  1717833600 AS created_at,
  1717833600 AS updated_at
FROM farms f
CROSS JOIN sensor_types s;

SELECT setval('sensors_id_seq', (SELECT COALESCE(MAX(id), 1) FROM sensors));

SET session_replication_role = 'origin';