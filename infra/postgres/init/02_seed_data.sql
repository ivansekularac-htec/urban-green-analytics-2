-- ROLES

INSERT INTO roles (id, name, description)
VALUES
(1, 'Farm Manager', 'Manager responsible for farm operations'),
(2, 'Operations Lead', 'Team responsible for operational activities'),
(3, 'Admin', 'System administrator');

SELECT setval(
    pg_get_serial_sequence('roles', 'id'),
    (SELECT MAX(id) FROM roles)
);

-- QUALITY GRADES

INSERT INTO quality_grades (id, code, name, description)
VALUES
(1, 'A', 'Grade A', 'Highest quality'),
(2, 'B', 'Grade B', 'Good quality'),
(3, 'C', 'Grade C', 'Acceptable quality'),
(4, 'D', 'Grade D', 'Lower grade quality'),
(5, 'E', 'Grade E', 'Production grade');

SELECT setval(
    pg_get_serial_sequence('quality_grades', 'id'),
    (SELECT MAX(id) FROM quality_grades)
);

-- INFRASTRUCTURE TYPES

INSERT INTO farm_infrastructure_types (id, name, description)
VALUES
(1, 'Hydroponic', 'Soilless growing system'),
(2, 'Aeroponic', 'Integrated aquaculture growing system');

SELECT setval(
    pg_get_serial_sequence('farm_infrastructure_types', 'id'),
    (SELECT MAX(id) FROM farm_infrastructure_types)
);

-- GROWING SYSTEM TYPES

INSERT INTO growing_system_types (id, name, description)
VALUES
(1, 'Vertical Farming', 'Plants grown vertically'),
(2, 'Tower Farming', 'Cylindrical growing towers'),
(3, 'Flat Bed Farming', 'Crops grown on flat beds');

SELECT setval(
    pg_get_serial_sequence('growing_system_types', 'id'),
    (SELECT MAX(id) FROM growing_system_types)
);

-- CROP CATEGORIES

INSERT INTO crop_categories (id, name, description)
VALUES
(1, 'Leafy Greens', 'Fast-growing leafy vegetables'),
(2, 'Herbs', 'Aromatic plants'),
(3, 'Microgreens', 'Young vegetable greens'),
(4, 'Specialty Crops', 'Unique premium crops');

SELECT setval(
    pg_get_serial_sequence('crop_categories', 'id'),
    (SELECT MAX(id) FROM crop_categories)
);

-- SENSOR TYPES

INSERT INTO sensor_types (id, name, unit, description, optimal_min, optimal_max)
VALUES
(1, 'Temperature', '°C', 'Ambient temperature', 18, 25),
(2, 'Humidity', '%', 'Relative humidity', 50, 70),
(3, 'Light Intensity', 'PPFD', 'Photosynthetic light intensity', 200, 800),
(4, 'pH Level', 'pH', 'Acidity/alkalinity level', 5, 7),
(5, 'Energy Usage', 'kWh', 'Total electricity consumption', 1, 1000000),
(6, 'CO2 Concentration', 'ppm', 'Carbon dioxide concentration', 400, 1200);

SELECT setval(
    pg_get_serial_sequence('sensor_types', 'id'),
    (SELECT MAX(id) FROM sensor_types)
);

-- CROPS

INSERT INTO crops (id, category_id, name, description)
VALUES
(1, 2, 'Basil', 'Aromatic herb'),
(2, 2, 'Mint', 'Refreshing herb'),
(3, 2, 'Parsley', 'Versatile herb'),
(4, 2, 'Cilantro', 'Herb with distinctive flavor'),
(5, 2, 'Thyme', 'Small-leaved herb'),
(6, 2, 'Rosemary', 'Fragrant woody herb'),

(7, 1, 'Romaine Lettuce', 'Crisp lettuce'),
(8, 1, 'Butterhead Lettuce', 'Soft lettuce'),
(9, 1, 'Arugula Lettuce', 'Peppery leafy green'),
(10, 1, 'Spinach', 'Tender nutrient-rich leaves'),
(11, 1, 'Kale', 'Leafy green vegetable'),
(12, 1, 'Swiss Chard', 'Leafy green with colorful stems'),

(13, 3, 'Radish', 'Spicy microgreen'),
(14, 3, 'Pea Shoots', 'Tender sweet shoots'),
(15, 3, 'Sunflower', 'Crunchy microgreen'),
(16, 3, 'Broccoli', 'Mild nutrient-rich microgreen'),

(17, 4, 'Nasturtium', 'Vibrant edible flower'),
(18, 4, 'Viola', 'Delicate edible flower'),
(19, 4, 'Baby Bok Choy', 'Tender compact vegetable');

SELECT setval(
    pg_get_serial_sequence('crops', 'id'),
    (SELECT MAX(id) FROM crops)
);

-- FARMS

WITH farm_seed (id, name, city, size_m2, infrastructure_type_name, growing_system_type_name, status, growing_beds_count)
AS (
    VALUES
    (1, 'UG Farm 001', 'Berlin', 265, 'Aeroponic', 'Tower Farming', 'active', 93),
    (2, 'UG Farm 002', 'Munich', 124, 'Aeroponic', 'Flat Bed Farming', 'active', 22),
    (3, 'UG Farm 003', 'Hamburg', 287, 'Aeroponic', 'Flat Bed Farming', 'active', 37),
    (4, 'UG Farm 004', 'Frankfurt', 119, 'Aeroponic', 'Tower Farming', 'active', 63),
    (5, 'UG Farm 005', 'Cologne', 135, 'Aeroponic', 'Vertical Farming', 'active', 80),
    (6, 'UG Farm 006', 'Stuttgart', 317, 'Aeroponic', 'Flat Bed Farming', 'active', 25),
    (7, 'UG Farm 007', 'Düsseldorf', 214, 'Aeroponic', 'Flat Bed Farming', 'active', 84),
    (8, 'UG Farm 008', 'Berlin', 303, 'Aeroponic', 'Vertical Farming', 'active', 15),
    (9, 'UG Farm 009', 'Munich', 385, 'Aeroponic', 'Tower Farming', 'active', 63),
    (10, 'UG Farm 010', 'Hamburg', 173, 'Aeroponic', 'Flat Bed Farming', 'active', 49),
    (11, 'UG Farm 011', 'Frankfurt', 386, 'Aeroponic', 'Vertical Farming', 'active', 84),
    (12, 'UG Farm 012', 'Cologne', 392, 'Aeroponic', 'Tower Farming', 'active', 22),
    (13, 'UG Farm 013', 'Stuttgart', 380, 'Aeroponic', 'Flat Bed Farming', 'active', 17),
    (14, 'UG Farm 014', 'Düsseldorf', 416, 'Aeroponic', 'Tower Farming', 'active', 97),
    (15, 'UG Farm 015', 'Berlin', 372, 'Hydroponic', 'Tower Farming', 'active', 69),
    (16, 'UG Farm 016', 'Munich', 399, 'Hydroponic', 'Tower Farming', 'active', 48),
    (17, 'UG Farm 017', 'Hamburg', 227, 'Aeroponic', 'Flat Bed Farming', 'active', 41),
    (18, 'UG Farm 018', 'Frankfurt', 141, 'Hydroponic', 'Flat Bed Farming', 'active', 73),
    (19, 'UG Farm 019', 'Cologne', 275, 'Hydroponic', 'Tower Farming', 'active', 87),
    (20, 'UG Farm 020', 'Stuttgart', 137, 'Aeroponic', 'Flat Bed Farming', 'active', 63),
    (21, 'UG Farm 021', 'Düsseldorf', 184, 'Hydroponic', 'Vertical Farming', 'active', 72),
    (22, 'UG Farm 022', 'Berlin', 315, 'Aeroponic', 'Flat Bed Farming', 'active', 19),
    (23, 'UG Farm 023', 'Munich', 491, 'Hydroponic', 'Tower Farming', 'active', 98),
    (24, 'UG Farm 024', 'Hamburg', 279, 'Hydroponic', 'Flat Bed Farming', 'active', 68),
    (25, 'UG Farm 025', 'Frankfurt', 135, 'Aeroponic', 'Tower Farming', 'active', 70),
    (26, 'UG Farm 026', 'Cologne', 456, 'Aeroponic', 'Vertical Farming', 'active', 99),
    (27, 'UG Farm 027', 'Stuttgart', 258, 'Hydroponic', 'Tower Farming', 'active', 59),
    (28, 'UG Farm 028', 'Düsseldorf', 442, 'Hydroponic', 'Vertical Farming', 'active', 69),
    (29, 'UG Farm 029', 'Berlin', 281, 'Aeroponic', 'Flat Bed Farming', 'active', 24),
    (30, 'UG Farm 030', 'Munich', 352, 'Aeroponic', 'Vertical Farming', 'active', 46),
    (31, 'UG Farm 031', 'Hamburg', 166, 'Aeroponic', 'Tower Farming', 'active', 60),
    (32, 'UG Farm 032', 'Frankfurt', 354, 'Aeroponic', 'Vertical Farming', 'active', 67),
    (33, 'UG Farm 033', 'Cologne', 305, 'Hydroponic', 'Vertical Farming', 'active', 65),
    (34, 'UG Farm 034', 'Stuttgart', 381, 'Hydroponic', 'Flat Bed Farming', 'active', 63),
    (35, 'UG Farm 035', 'Düsseldorf', 283, 'Hydroponic', 'Vertical Farming', 'active', 29),
    (36, 'UG Farm 036', 'Berlin', 142, 'Aeroponic', 'Vertical Farming', 'active', 39),
    (37, 'UG Farm 037', 'Munich', 437, 'Aeroponic', 'Vertical Farming', 'active', 72),
    (38, 'UG Farm 038', 'Hamburg', 401, 'Aeroponic', 'Tower Farming', 'active', 46),
    (39, 'UG Farm 039', 'Frankfurt', 102, 'Aeroponic', 'Tower Farming', 'active', 78),
    (40, 'UG Farm 040', 'Cologne', 289, 'Hydroponic', 'Vertical Farming', 'active', 98),
    (41, 'UG Farm 041', 'Stuttgart', 363, 'Aeroponic', 'Tower Farming', 'active', 97),
    (42, 'UG Farm 042', 'Düsseldorf', 386, 'Hydroponic', 'Tower Farming', 'active', 61),
    (43, 'UG Farm 043', 'Berlin', 301, 'Aeroponic', 'Tower Farming', 'active', 91),
    (44, 'UG Farm 044', 'Munich', 305, 'Aeroponic', 'Vertical Farming', 'active', 18),
    (45, 'UG Farm 045', 'Hamburg', 206, 'Hydroponic', 'Vertical Farming', 'active', 24),
    (46, 'UG Farm 046', 'Frankfurt', 274, 'Aeroponic', 'Vertical Farming', 'active', 10),
    (47, 'UG Farm 047', 'Cologne', 390, 'Aeroponic', 'Flat Bed Farming', 'active', 22),
    (48, 'UG Farm 048', 'Stuttgart', 286, 'Aeroponic', 'Vertical Farming', 'active', 36),
    (49, 'UG Farm 049', 'Düsseldorf', 414, 'Hydroponic', 'Vertical Farming', 'active', 91),
    (50, 'UG Farm 050', 'Berlin', 229, 'Hydroponic', 'Flat Bed Farming', 'active', 56),
    (51, 'UG Farm 051', 'Munich', 342, 'Aeroponic', 'Vertical Farming', 'active', 72),
    (52, 'UG Farm 052', 'Hamburg', 338, 'Hydroponic', 'Tower Farming', 'active', 49),
    (53, 'UG Farm 053', 'Frankfurt', 143, 'Aeroponic', 'Vertical Farming', 'active', 53),
    (54, 'UG Farm 054', 'Cologne', 479, 'Hydroponic', 'Tower Farming', 'active', 98),
    (55, 'UG Farm 055', 'Stuttgart', 182, 'Aeroponic', 'Vertical Farming', 'active', 77),
    (56, 'UG Farm 056', 'Düsseldorf', 285, 'Aeroponic', 'Flat Bed Farming', 'active', 79),
    (57, 'UG Farm 057', 'Berlin', 113, 'Hydroponic', 'Flat Bed Farming', 'active', 21),
    (58, 'UG Farm 058', 'Munich', 456, 'Hydroponic', 'Flat Bed Farming', 'active', 56),
    (59, 'UG Farm 059', 'Hamburg', 185, 'Hydroponic', 'Vertical Farming', 'active', 78),
    (60, 'UG Farm 060', 'Frankfurt', 377, 'Hydroponic', 'Flat Bed Farming', 'active', 38),
    (61, 'UG Farm 061', 'Cologne', 413, 'Aeroponic', 'Vertical Farming', 'active', 61),
    (62, 'UG Farm 062', 'Stuttgart', 478, 'Aeroponic', 'Vertical Farming', 'active', 76),
    (63, 'UG Farm 063', 'Düsseldorf', 352, 'Hydroponic', 'Flat Bed Farming', 'active', 13),
    (64, 'UG Farm 064', 'Berlin', 114, 'Hydroponic', 'Tower Farming', 'active', 43),
    (65, 'UG Farm 065', 'Munich', 199, 'Hydroponic', 'Tower Farming', 'active', 54),
    (66, 'UG Farm 066', 'Hamburg', 286, 'Aeroponic', 'Vertical Farming', 'active', 23),
    (67, 'UG Farm 067', 'Frankfurt', 216, 'Hydroponic', 'Vertical Farming', 'active', 53),
    (68, 'UG Farm 068', 'Cologne', 204, 'Hydroponic', 'Flat Bed Farming', 'active', 88),
    (69, 'UG Farm 069', 'Stuttgart', 100, 'Hydroponic', 'Flat Bed Farming', 'active', 54),
    (70, 'UG Farm 070', 'Düsseldorf', 429, 'Aeroponic', 'Flat Bed Farming', 'active', 25),
    (71, 'UG Farm 071', 'Berlin', 298, 'Aeroponic', 'Tower Farming', 'active', 32),
    (72, 'UG Farm 072', 'Munich', 322, 'Hydroponic', 'Vertical Farming', 'active', 60),
    (73, 'UG Farm 073', 'Hamburg', 337, 'Hydroponic', 'Flat Bed Farming', 'active', 20),
    (74, 'UG Farm 074', 'Frankfurt', 471, 'Aeroponic', 'Vertical Farming', 'active', 26),
    (75, 'UG Farm 075', 'Cologne', 114, 'Aeroponic', 'Flat Bed Farming', 'active', 69)
)
INSERT INTO farms (id, name, city, size_m2, infrastructure_type_id, growing_system_type_id, status, growing_beds_count)
SELECT
    fs.id,
    fs.name,
    fs.city,
    fs.size_m2,
    fit.id,
    gst.id,
    fs.status::farm_status,
    fs.growing_beds_count
FROM farm_seed fs
JOIN farm_infrastructure_types fit
    ON fit.name = fs.infrastructure_type_name
JOIN growing_system_types gst
    ON gst.name = fs.growing_system_type_name;

SELECT setval(
    pg_get_serial_sequence('farms', 'id'), 
    (SELECT MAX(id) FROM farms)
);

-- HARVESTS

CREATE TEMP TABLE harvests_staging (
    farm_id BIGINT,
    crop_id BIGINT,
    weight_kg DECIMAL(10, 3),
    grade_id BIGINT,
    created_at BIGINT,
    updated_at BIGINT
);

COPY harvests_staging (farm_id, crop_id, weight_kg, grade_id, created_at, updated_at)
FROM PROGRAM 'gunzip -c /data/harvests.csv.gz'
WITH (
    FORMAT csv,
    HEADER true,
    NULL ''
);

INSERT INTO harvests (farm_id, crop_id, quality_grade_id, weight_kg, created_at, updated_at)
SELECT
    farm_id,
    crop_id,
    grade_id,
    weight_kg,
    created_at,
    updated_at
FROM harvests_staging;

SELECT setval(
    pg_get_serial_sequence('harvests', 'id'),
    (SELECT MAX(id) FROM harvests)
);

-- SENSORS

INSERT INTO sensors (farm_id, sensor_type_id, serial_number, status)
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
        LPAD(((f.id - 1) * 6 + st.id)::TEXT, 3, '0')
    ) AS serial_number,
    'active'::sensor_status AS status
FROM farms f
CROSS JOIN sensor_types st;

SELECT setval(
    pg_get_serial_sequence('sensors', 'id'),
    (SELECT MAX(id) FROM sensors)
);
