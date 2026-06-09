-- ROLES

INSERT INTO roles (name, description)
VALUES
('Farm Manager', 'Manager responsible for specific farm'),
('Operations Team', 'Team responsible for daily farm operations'),
('Admin', 'System administrator with full privileges');


-- CROP CATEGORY

INSERT INTO crop_categories (name, description)
VALUES
('Leafy Greens', 'Fast-growing vegetables valued for their edible leaves, typically harvested young for optimal tenderness and flavor'),
('Herbs', 'Aromatic plants used for flavoring, garnishing, or medicinal purposes, often requiring specific growing conditions for optimal oil content'),
('Microgreens', 'Young vegetable greens harvested 1-3 weeks after germination, prized for intense flavor and high nutrient density'),
('Specialty Crops', 'Unique, premium produce such as edible flowers and baby bok choy, cultivated to meet niche market demands and offer higher profit margins.');


-- GROWING SYSTEM TYPE

INSERT INTO growing_system_types (name, description)
VALUES
('Vertical Farming', 'Plants grown in vertically stacked layers with artificial LED lighting and precise nutrient delivery systems'),
('Tower Farming', 'Cylindrical or tower-shaped growing structures that maximize vertical space while minimizing floor footprint'),
('Flat Bed Farming', 'Crops grown on level, flat soil beds allowing uniform irrigation, easy planting, and mechanized field operations');


-- INFRASTRUCTURE TYPE

INSERT INTO infrastructure_types (name, description)
VALUES
('Hydroponic', 'Soilless growing system where plants receive nutrients through mineral-rich water solutions in controlled environments'),
('Aquaponic', 'Integrated system combining fish farming with plant cultivation, where fish waste provides nutrients for plants'),
('Aeroponic', 'Plants are grown with roots suspended in air and periodically misted with nutrient-rich solution');


--QUALITY GRADES

INSERT INTO quality_grades (code, name, description)
VALUES
('A', 'Premium', 'Highest quality produce with perfect appearance, optimal size, and superior taste - suitable for high-end retail and restaurants'),
('B', 'Standard', 'Good quality produce with minor cosmetic imperfections but excellent nutritional value - ideal for general retail markets'),
('C', 'Commercial', 'Acceptable quality with noticeable cosmetic flaws but good nutritional content - suitable for food service and wholesale'),
('D', 'Processing', 'Lower grade produce with significant cosmetic issues but safe for consumption - used for processed foods, juices, and sauces'),
('E', 'Livestock Feed', 'Produce not suitable for human consumption due to quality issues - repurposed as animal feed or compost material');


-- SENSOR TYPE

INSERT INTO sensor_types (name, unit, description, optimal_min, optimal_max)
VALUES
('Temperature', '°C', 'Ambient temperature measurement', 18, 25),
('Humidity', '%', 'Relative humidity percentage', 50, 70),
('Light Intensity', 'PPFD', 'Photosynthetic photon flux density', 200, 800),
('pH Level', 'pH', 'Acidity/alkalinity of water or soil', 5, 7),
('Energy Usage', 'kWh', 'Total electrical energy consumed by the system', 1, 1000000),
('CO2 Concentration', 'ppm', 'Carbon dioxide parts per million', 400, 1200);



-- FARMS

CREATE TEMP TABLE farms_staging (
    farm_id BIGINT,
    name VARCHAR(255),
    city VARCHAR(255),
    size_m2 DECIMAL(10,3),
    infrastructure_type VARCHAR(255),
    growing_system_type VARCHAR(255),
    growing_beds_count INTEGER
);

COPY farms_staging (
    farm_id,
    name,
    city,
    size_m2,
    infrastructure_type,
    growing_system_type,
    growing_beds_count
)
FROM '/data/farms.csv'
WITH (FORMAT csv, HEADER true);

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
    it.id AS infrastructure_type_id,
    gst.id AS growing_system_type_id,
    fs.name,
    fs.city,
    fs.size_m2,
    'ACTIVE'::farm_status,
    fs.growing_beds_count
FROM farms_staging fs
JOIN infrastructure_types it
    ON it.name = fs.infrastructure_type
JOIN growing_system_types gst
    ON gst.name = fs.growing_system_type;


-- CROPS

CREATE TEMP TABLE crops_staging (
    crop_id BIGINT,
    crop_name VARCHAR(255),
    crop_category VARCHAR(255),
    description VARCHAR(255)
);

COPY crops_staging (
    crop_id,
    crop_name,
    crop_category,
    description
)
FROM '/data/crops.csv'
WITH (FORMAT csv, HEADER true);

INSERT INTO crops (
    category_id,
    name,
    description
)
SELECT
    cc.id,
    cs.crop_name,
    cs.description
FROM crops_staging cs
JOIN crop_categories cc
    ON cc.name = cs.crop_category;


-- HARVESTS

CREATE TEMP TABLE harvests_staging (
    farm_id BIGINT,
    crop_id BIGINT,
    weight_kg DECIMAL(10,3),
    grade_id BIGINT,
    created_at BIGINT,
    updated_at BIGINT
);

COPY harvests_staging (
    farm_id,
    crop_id,
    weight_kg,
    grade_id,
    created_at,
    updated_at
)
FROM PROGRAM 'gunzip -c /data/harvests.csv.gz'
WITH (FORMAT csv, HEADER true, NULL '');

INSERT INTO harvests (
    farm_id,
    crop_id,
    quality_grade_id,
    weight_kg,
    created_at,
    updated_at
)
SELECT
    hs.farm_id,
    hs.crop_id,
    hs.grade_id,
    hs.weight_kg,
    hs.created_at,
    hs.updated_at
FROM harvests_staging hs
JOIN farms f
    ON f.id = hs.farm_id
JOIN crops c
    ON c.id = hs.crop_id
JOIN quality_grades qg
    ON qg.id = hs.grade_id;


-- SENSORS

INSERT INTO sensors (
    farm_id,
    sensor_type_id,
    serial_number,
    status,
    installed_at
)
SELECT
    f.id AS farm_id,
    st.id AS sensor_type_id,

    CONCAT(
        CASE st.id
            WHEN 1 THEN 'TEMP-20240315-'
            WHEN 2 THEN 'HUM-20240322-'
            WHEN 3 THEN 'LIGHT-20240320-'
            WHEN 4 THEN 'PH-20240318-'
            WHEN 5 THEN 'ENER-20240325-'
            WHEN 6 THEN 'CO2-20240319-'
        END,
        LPAD(((f.id - 1) * 6 + st.id)::text, 3, '0')
    ) AS serial_number,

    'ACTIVE'::sensor_status AS status,

    EXTRACT(EPOCH FROM NOW())::BIGINT AS installed_at

FROM farms f
CROSS JOIN sensor_types st;


-- FARM CROPS

INSERT INTO farm_crops (
    farm_id,
    crop_id,
    started_at,
    ended_at
)
SELECT
    f.id,
    c.id,
    EXTRACT(
        EPOCH FROM NOW() - (random() * 180 || ' days')::INTERVAL
    )::BIGINT,
    NULL
FROM farms f
CROSS JOIN crops c;