-- ============================================================
-- Roles
-- ============================================================

COPY urbangreen.roles (
    role_id,
    name,
    description
)
FROM '/data/roles.csv'
WITH (FORMAT csv, HEADER true, NULL '');


-- ============================================================
-- Infrastructure types
-- ============================================================
COPY urbangreen.farm_infrastructure_types (
    farm_infrastructure_type_id,
    name,
    description
)
FROM '/data/infrastructure_types.csv'
WITH (FORMAT csv, HEADER true, NULL '');


-- ============================================================
-- Growing system types
-- ============================================================
COPY urbangreen.growing_system_types (
    growing_system_type_id,
    name,
    description
)
FROM '/data/growing_system_types.csv'
WITH (FORMAT csv, HEADER true, NULL '');


-- ============================================================
-- Sensor types
-- ============================================================
COPY urbangreen.sensor_types (
    sensor_type_id,
    name,
    unit,
    description,
    optimal_min,
    optimal_max
)
FROM '/data/sensor_types.csv'
WITH (FORMAT csv, HEADER true, NULL '');


-- ============================================================
-- Crop categories
-- ============================================================
COPY urbangreen.crop_categories (
    crop_category_id,
    name,
    description
)
FROM '/data/crop_categories.csv'
WITH (FORMAT csv, HEADER true, NULL '');


-- ============================================================
-- Quality grades
-- ============================================================
CREATE TEMP TABLE staging_quality_grades (
    quality_grade_id BIGINT,
    name VARCHAR,
    description VARCHAR
);

COPY staging_quality_grades
FROM '/data/quality_grades.csv'
WITH (FORMAT csv, HEADER true, NULL '');

INSERT INTO urbangreen.quality_grades (
    quality_grade_id,
    code,
    name,
    description
)
SELECT
    quality_grade_id,
    SPLIT_PART(name, ' ', 2) AS code,
    name,
    description
FROM staging_quality_grades;


-- ============================================================
-- Crops
-- ============================================================
CREATE TEMP TABLE staging_crops (
    crop_id BIGINT,
    name VARCHAR,
    crop_category_name VARCHAR,
    description VARCHAR
);

COPY staging_crops
FROM '/data/crops.csv'
WITH (FORMAT csv, HEADER true, NULL '');

INSERT INTO urbangreen.crops (
    crop_id,
    crop_category_id,
    name,
    description
)
SELECT
    sc.crop_id,
    cc.crop_category_id,
    sc.name,
    sc.description
FROM staging_crops sc
JOIN urbangreen.crop_categories cc
    ON cc.name = sc.crop_category_name;


-- ============================================================
-- Farms
-- ============================================================
CREATE TEMP TABLE staging_farms (
    farm_id BIGINT,
    name VARCHAR,
    city VARCHAR,
    size_m2 DECIMAL(10,3),
    infrastructure_type_name VARCHAR,
    growing_system_type_name VARCHAR,
    growing_beds_count INT
);

COPY staging_farms
FROM '/data/farms.csv'
WITH (FORMAT csv, HEADER true, NULL '');

INSERT INTO urbangreen.farms (
    farm_id,
    farm_infrastructure_type_id,
    growing_system_type_id,
    name,
    city,
    size_m2,
    status,
    growing_beds_count
)
SELECT
    sf.farm_id,
    fit.farm_infrastructure_type_id,
    gst.growing_system_type_id,
    sf.name,
    sf.city,
    sf.size_m2,
    'ACTIVE'::urbangreen.farm_status,
    sf.growing_beds_count
FROM staging_farms sf
JOIN urbangreen.farm_infrastructure_types fit
    ON fit.name = sf.infrastructure_type_name
JOIN urbangreen.growing_system_types gst
    ON gst.name = sf.growing_system_type_name;


-- ============================================================
-- Harvests
-- ============================================================

CREATE TEMP TABLE staging_harvests (
    farm_id BIGINT,
    crop_id BIGINT,
    weight_kg DECIMAL(10,3),
    quality_grade_id BIGINT,
    created_at BIGINT,
    updated_at BIGINT
);

COPY staging_harvests (
    farm_id,
    crop_id,
    weight_kg,
    quality_grade_id,
    created_at,
    updated_at
)
FROM PROGRAM 'gunzip -c /data/harvests.csv.gz'
WITH (FORMAT csv, HEADER true, NULL '');

INSERT INTO urbangreen.harvests (
    farm_id,
    crop_id,
    quality_grade_id,
    weight_kg,
    created_at,
    updated_at
)
SELECT
    farm_id,
    crop_id,
    quality_grade_id,
    weight_kg,
    created_at,
    updated_at
FROM staging_harvests;


-- ============================================================
-- Align id with the maximum IDs loaded from CSV
-- so future inserts continue without PK conflicts
-- ============================================================
SELECT setval(pg_get_serial_sequence('urbangreen.roles', 'role_id'), (SELECT COALESCE(MAX(role_id), 1) FROM urbangreen.roles));
SELECT setval(pg_get_serial_sequence('urbangreen.farm_infrastructure_types', 'farm_infrastructure_type_id'), (SELECT COALESCE(MAX(farm_infrastructure_type_id), 1) FROM urbangreen.farm_infrastructure_types));
SELECT setval(pg_get_serial_sequence('urbangreen.growing_system_types', 'growing_system_type_id'), (SELECT COALESCE(MAX(growing_system_type_id), 1) FROM urbangreen.growing_system_types));
SELECT setval(pg_get_serial_sequence('urbangreen.sensor_types', 'sensor_type_id'), (SELECT COALESCE(MAX(sensor_type_id), 1) FROM urbangreen.sensor_types));
SELECT setval(pg_get_serial_sequence('urbangreen.crop_categories', 'crop_category_id'), (SELECT COALESCE(MAX(crop_category_id), 1) FROM urbangreen.crop_categories));
SELECT setval(pg_get_serial_sequence('urbangreen.quality_grades', 'quality_grade_id'), (SELECT COALESCE(MAX(quality_grade_id), 1) FROM urbangreen.quality_grades));
SELECT setval(pg_get_serial_sequence('urbangreen.crops', 'crop_id'), (SELECT COALESCE(MAX(crop_id), 1) FROM urbangreen.crops));
SELECT setval(pg_get_serial_sequence('urbangreen.farms', 'farm_id'), (SELECT COALESCE(MAX(farm_id), 1) FROM urbangreen.farms));
SELECT setval(pg_get_serial_sequence('urbangreen.harvests', 'harvest_id'), (SELECT COALESCE(MAX(harvest_id), 1) FROM urbangreen.harvests));