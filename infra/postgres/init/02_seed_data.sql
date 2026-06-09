INSERT INTO roles (
    name,
    description
)
VALUES
    ('Farm Manager', 'Manager responsible for specific farm'),
    ('Operations Team', 'Team responsible for daily farm operations'),
    ('Admin', 'System administrator with full privileges')
ON CONFLICT (name) DO NOTHING;

-- 1. ISPRAVLJENO: farm_infrastructure_types umesto infrastructure_types
INSERT INTO farm_infrastructure_types (
    name,
    description
)
VALUES
(
    'Hydroponic',
    'Soilless growing system where plants receive nutrients through mineral-rich water solutions in controlled environments'
),
(
    'Aeroponic',
    'Integrated system combining fish farming with plant cultivation, where fish waste provides nutrients for plants'
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO growing_system_types (
    name,
    description
)
VALUES
(
    'Vertical Farming',
    'Plants grown in vertically stacked layers with artificial LED lighting and precise nutrient delivery systems'
),
(
    'Tower Farming',
    'Cylindrical or tower-shaped growing structures that maximize vertical space while minimizing floor footprint'
),
(
    'Flat Bed Farming',
    'Crops grown on level, flat soil beds allowing uniform irrigation, easy planting, and mechanized field operations'
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO sensor_types (
    name,
    unit,
    description,
    optimal_min,
    optimal_max
)
VALUES
(
    'Temperature',
    '°C',
    'Ambient temperature measurement',
    18,
    25
),
(
    'Humidity',
    '%',
    'Relative humidity percentage',
    50,
    70
),
(
    'Light Intensity',
    'PPFD',
    'Photosynthetic photon flux density',
    200,
    800
),
(
    'pH Level',
    'pH',
    'Acidity/alkalinity of water or soil',
    5,
    7
),
(
    'Energy Usage',
    'kWh',
    'Total electrical energy consumed by the system',
    1,
    1000000
),
(
    'CO2 Concentration',
    'ppm',
    'Carbon dioxide parts per million',
    400,
    1200
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO crop_categories (
    name,
    description
)
VALUES
(
    'Leafy Greens',
    'Fast-growing vegetables valued for their edible leaves, typically harvested young for optimal tenderness and flavor'
),
(
    'Herbs',
    'Aromatic plants used for flavoring, garnishing, or medicinal purposes, often requiring specific growing conditions for optimal oil content'
),
(
    'Microgreens',
    'Young vegetable greens harvested 1-3 weeks after germination, prized for intense flavor and high nutrient density'
),
(
    'Specialty Crops',
    'Unique, premium produce such as edible flowers and baby bok choy, cultivated to meet niche market demands and offer higher profit margins.'
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO quality_grades (
    code,
    name,
    description
)
VALUES
(
    'A',
    'Premium',
    'Highest quality produce with perfect appearance, optimal size, and superior taste - suitable for high-end retail and restaurants'
),
(
    'B',
    'Standard',
    'Good quality produce with minor cosmetic imperfections but excellent nutritional value - ideal for general retail markets'
),
(
    'C',
    'Commercial',
    'Acceptable quality with noticeable cosmetic flaws but good nutritional content - suitable for food service and wholesale'
),
(
    'D',
    'Processing',
    'Lower grade produce with significant cosmetic issues but safe for consumption - used for processed foods, juices, and sauces'
),
(
    'E',
    'Livestock Feed',
    'Produce not suitable for human consumption due to quality issues - repurposed as animal feed or compost material'
)
ON CONFLICT (code) DO NOTHING;

CREATE TEMP TABLE farm_import (
    farm_id INTEGER,
    name VARCHAR(100),
    city VARCHAR(100),
    size_m2 DECIMAL(10,3),
    infrastructure_type VARCHAR(100),
    growing_system_type VARCHAR(100),
    growing_beds_count INTEGER
);

COPY farm_import
FROM '/data/farms.csv'
DELIMITER ','
CSV HEADER;

INSERT INTO farms (
    infrastructure_type_id,
    growing_system_type_id,
    name,
    city,
    size_m2,
    status,
    growing_beds_count
)
SELECT
    -- 2. ISPRAVLJENO: farm_infrastructure_types umesto infrastructure_types
    farm_infrastructure_types.id,
    growing_system_types.id,
    farm_import.name,
    farm_import.city,
    farm_import.size_m2,
    'active'::farm_status, -- 3. ISPRAVLJENO: mala slova 'active' da se poklopi sa ENUM-om u šemi
    farm_import.growing_beds_count
FROM farm_import
-- 4. ISPRAVLJENO: farm_infrastructure_types u JOIN-u
JOIN farm_infrastructure_types
    ON farm_infrastructure_types.name = farm_import.infrastructure_type
JOIN growing_system_types
    ON growing_system_types.name = farm_import.growing_system_type;

CREATE TEMP TABLE crop_import (
    crop_id INTEGER,
    crop_name VARCHAR(100),
    crop_category VARCHAR(100),
    description VARCHAR(500)
);

COPY crop_import
FROM '/data/crops.csv'
DELIMITER ','
CSV HEADER;

INSERT INTO crops (
    category_id,
    name,
    description
)
SELECT
    crop_categories.id,
    crop_import.crop_name,
    crop_import.description
FROM crop_import
JOIN crop_categories
    ON crop_categories.name = crop_import.crop_category;

COPY public.harvests (farm_id, crop_id, weight_kg, quality_grade_id, created_at, updated_at)
FROM PROGRAM 'gunzip -c /data/harvests.csv.gz'
WITH (FORMAT csv, HEADER true, NULL '');

-- Reset sequence za harvests pošto punimo spolja
SELECT setval('public.harvests_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.harvests));

INSERT INTO public.sensors (farm_id, sensor_type_id, serial_number, status)
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
  'active'::sensor_status AS status -- 5. ISPRAVLJENO: mala slova 'active'
FROM generate_series(1, 75) AS f(id)
CROSS JOIN generate_series(1, 6) AS s(id);

INSERT INTO farm_crops (farm_id, crop_id, started_at)
SELECT
    farms.id,
    crops.id,
    EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
FROM farms
CROSS JOIN crops;