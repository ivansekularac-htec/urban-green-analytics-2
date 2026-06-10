CREATE SCHEMA IF NOT EXISTS app;
SET search_path TO app;

INSERT INTO roles (
    id,
    name,
    description
)
VALUES
(1, 'Farm Manager', 'Manager responsible for specific farm'),
(2, 'Operations Team', 'Team responsible for daily farm operations'),
(3, 'Admin', 'System administrator with full privileges');

SELECT setval(
    'roles_id_seq',
    (SELECT MAX(id) FROM roles)
);

INSERT INTO sensor_types (
    id,
    name,
    unit,
    description,
    optimal_min,
    optimal_max   
)
VALUES
(1, 'Temperature', '°C' , 'Ambient temperature measurement', 18.0, 25.0),
(2, 'Humidity', '%' , 'Relative humidity percentage', 50.0, 70.0),
(3, 'Light Intensity', 'PPFD' , 'Photosynthetic photon flux density', 200.0, 800.0),
(4, 'pH Level', 'pH' , 'Acidity/alkalinity of water or soil', 5.0, 7.0),
(5, 'Energy Usage', 'kWh' , 'Total electrical energy consumed by the system', 1.0, 1000000.0),
(6, 'CO2 Concentration', 'ppm' , 'Carbon dioxide parts per million', 400.0, 1200.0);

SELECT setval(
    'sensor_types_id_seq',
    (SELECT MAX(id) FROM sensor_types)
);

INSERT INTO quality_grades (
    id,
    code,
    name,
    description   
)
VALUES
(1, 'A', 'Premium', 'Highest quality produce with perfect appearance, optimal size, and superior taste - suitable for high-end retail and restaurants'),
(2, 'B', 'Standard', 'Good quality produce with minor cosmetic imperfections but excellent nutritional value - ideal for general retail markets'),
(3, 'C', 'Commercial', 'Acceptable quality with noticeable cosmetic flaws but good nutritional content - suitable for food service and wholesale'),
(4, 'D', 'Processing', 'Lower grade produce with significant cosmetic issues but safe for consumption - used for processed foods, juices, and sauces'),
(5, 'E', 'Livestock Feed', 'Produce not suitable for human consumption due to quality issues - repurposed as animal feed or compost material');

SELECT setval(
    'quality_grades_id_seq',
    (SELECT MAX(id) FROM quality_grades)
);

INSERT INTO farm_infrastructure_types (
    id,
    name,
    description 
)
VALUES
(1, 'Hydroponic', 'Soilless cultivation method using nutrient-rich water solutions'),
(2, 'Aeroponic', 'Plants are grown in air and nourished through nutrient misting.');

SELECT setval(
    'farm_infrastructure_types_id_seq',
    (SELECT MAX(id) FROM farm_infrastructure_types)
);

INSERT INTO growing_system_types (
    id,
    name,
    description    
)
VALUES
(1, 'Vertical Farming', 'Plants grown in vertically stacked layers with artificial LED lighting and precise nutrient delivery systems'),
(2, 'Tower Farming', 'Cylindrical or tower-shaped growing structures that maximize vertical space while minimizing floor footprint'),
(3, 'Flat Bed Farming', 'Crops grown on level, flat soil beds allowing uniform irrigation, easy planting, and mechanized field operations');

SELECT setval(
    'growing_system_types_id_seq',
    (SELECT MAX(id) FROM growing_system_types)
);

INSERT INTO farms (
    id,
    infrastructure_type_id,
    growing_system_type_id,
    name,
    city,
    size_m2,
    status,
    growing_beds_count   
)
VALUES
(1, 2, 2, 'UG Farm 001', 'Berlin', 265.0, 'ACTIVE', 93),
(2, 2, 3, 'UG Farm 002', 'Munich', 124.0, 'ACTIVE', 22),
(3, 2, 3, 'UG Farm 003', 'Hamburg', 287.0, 'ACTIVE', 37),
(4, 2, 2, 'UG Farm 004', 'Frankfurt', 119.0, 'ACTIVE', 63),
(5, 2, 1, 'UG Farm 005', 'Cologne', 135.0, 'ACTIVE', 80),
(6, 2, 3, 'UG Farm 006', 'Stuttgart', 317.0, 'ACTIVE', 25),
(7, 2, 3, 'UG Farm 007', 'Düsseldorf', 214.0, 'ACTIVE', 84),
(8, 2, 1, 'UG Farm 008', 'Berlin', 303.0, 'ACTIVE', 15),
(9, 2, 2, 'UG Farm 009', 'Munich', 385.0, 'ACTIVE', 63),
(10, 2, 3, 'UG Farm 010', 'Hamburg', 173.0, 'ACTIVE', 49),
(11, 2, 1, 'UG Farm 011', 'Frankfurt', 386.0, 'ACTIVE', 84),
(12, 2, 2, 'UG Farm 012', 'Cologne', 392.0, 'ACTIVE', 22),
(13, 2, 3, 'UG Farm 013', 'Stuttgart', 380.0, 'ACTIVE', 17),
(14, 2, 2, 'UG Farm 014', 'Düsseldorf', 416.0, 'ACTIVE', 97),
(15, 1, 2, 'UG Farm 015', 'Berlin', 372.0, 'ACTIVE', 69),
(16, 1, 2, 'UG Farm 016', 'Munich', 399.0, 'ACTIVE', 48),
(17, 2, 3, 'UG Farm 017', 'Hamburg', 227.0, 'ACTIVE', 41),
(18, 1, 3, 'UG Farm 018', 'Frankfurt', 141.0, 'ACTIVE', 73),
(19, 1, 2, 'UG Farm 019', 'Cologne', 275.0, 'ACTIVE', 87),
(20, 2, 3, 'UG Farm 020', 'Stuttgart', 137.0, 'ACTIVE', 63),
(21, 1, 1, 'UG Farm 021', 'Düsseldorf', 184.0, 'ACTIVE', 72),
(22, 2, 3, 'UG Farm 022', 'Berlin', 315.0, 'ACTIVE', 19),
(23, 1, 2, 'UG Farm 023', 'Munich', 491.0, 'ACTIVE', 98),
(24, 1, 3, 'UG Farm 024', 'Hamburg', 279.0, 'ACTIVE', 68),
(25, 2, 2, 'UG Farm 025', 'Frankfurt', 135.0, 'ACTIVE', 70),
(26, 2, 1, 'UG Farm 026', 'Cologne', 456.0, 'ACTIVE', 99),
(27, 1, 2, 'UG Farm 027', 'Stuttgart', 258.0, 'ACTIVE', 59),
(28, 1, 1, 'UG Farm 028', 'Düsseldorf', 442.0, 'ACTIVE', 69),
(29, 2, 3, 'UG Farm 029', 'Berlin', 281.0, 'ACTIVE', 24),
(30, 2, 1, 'UG Farm 030', 'Munich', 352.0, 'ACTIVE', 46),
(31, 2, 2, 'UG Farm 031', 'Hamburg', 166.0, 'ACTIVE', 60),
(32, 2, 1, 'UG Farm 032', 'Frankfurt', 354.0, 'ACTIVE', 67),
(33, 1, 1, 'UG Farm 033', 'Cologne', 305.0, 'ACTIVE', 65),
(34, 1, 3, 'UG Farm 034', 'Stuttgart', 381.0, 'ACTIVE', 63),
(35, 1, 1, 'UG Farm 035', 'Düsseldorf', 283.0, 'ACTIVE', 29),
(36, 2, 1, 'UG Farm 036', 'Berlin', 142.0, 'ACTIVE', 39),
(37, 2, 1, 'UG Farm 037', 'Munich', 437.0, 'ACTIVE', 72),
(38, 2, 2, 'UG Farm 038', 'Hamburg', 401.0, 'ACTIVE', 46),
(39, 2, 2, 'UG Farm 039', 'Frankfurt', 102.0, 'ACTIVE', 78),
(40, 1, 1, 'UG Farm 040', 'Cologne', 289.0, 'ACTIVE', 98),
(41, 2, 2, 'UG Farm 041', 'Stuttgart', 363.0, 'ACTIVE', 97),
(42, 1, 2, 'UG Farm 042', 'Düsseldorf', 386.0, 'ACTIVE', 61),
(43, 2, 2, 'UG Farm 043', 'Berlin', 301.0, 'ACTIVE', 91),
(44, 2, 1, 'UG Farm 044', 'Munich', 305.0, 'ACTIVE', 18),
(45, 1, 1, 'UG Farm 045', 'Hamburg', 206.0, 'ACTIVE', 24),
(46, 2, 1, 'UG Farm 046', 'Frankfurt', 274.0, 'ACTIVE', 10),
(47, 2, 3, 'UG Farm 047', 'Cologne', 390.0, 'ACTIVE', 22),
(48, 2, 1, 'UG Farm 048', 'Stuttgart', 286.0, 'ACTIVE', 36),
(49, 1, 1, 'UG Farm 049', 'Düsseldorf', 414.0, 'ACTIVE', 91),
(50, 1, 3, 'UG Farm 050', 'Berlin', 229.0, 'ACTIVE', 56),
(51, 2, 1, 'UG Farm 051', 'Munich', 342.0, 'ACTIVE', 72),
(52, 1, 2, 'UG Farm 052', 'Hamburg', 338.0, 'ACTIVE', 49),
(53, 2, 1, 'UG Farm 053', 'Frankfurt', 143.0, 'ACTIVE', 53),
(54, 1, 2, 'UG Farm 054', 'Cologne', 479.0, 'ACTIVE', 98),
(55, 2, 1, 'UG Farm 055', 'Stuttgart', 182.0, 'ACTIVE', 77),
(56, 2, 3, 'UG Farm 056', 'Düsseldorf', 285.0, 'ACTIVE', 79),
(57, 1, 3, 'UG Farm 057', 'Berlin', 113.0, 'ACTIVE', 21),
(58, 1, 3, 'UG Farm 058', 'Munich', 456.0, 'ACTIVE', 56),
(59, 1, 1, 'UG Farm 059', 'Hamburg', 185.0, 'ACTIVE', 78),
(60, 1, 3, 'UG Farm 060', 'Frankfurt', 377.0, 'ACTIVE', 38),
(61, 2, 1, 'UG Farm 061', 'Cologne', 413.0, 'ACTIVE', 61),
(62, 2, 1, 'UG Farm 062', 'Stuttgart', 478.0, 'ACTIVE', 76),
(63, 1, 3, 'UG Farm 063', 'Düsseldorf', 352.0, 'ACTIVE', 13),
(64, 1, 2, 'UG Farm 064', 'Berlin', 114.0, 'ACTIVE', 43),
(65, 1, 2, 'UG Farm 065', 'Munich', 199.0, 'ACTIVE', 54),
(66, 2, 1, 'UG Farm 066', 'Hamburg', 286.0, 'ACTIVE', 23),
(67, 1, 1, 'UG Farm 067', 'Frankfurt', 216.0, 'ACTIVE', 53),
(68, 1, 3, 'UG Farm 068', 'Cologne', 204.0, 'ACTIVE', 88),
(69, 1, 3, 'UG Farm 069', 'Stuttgart', 100.0, 'ACTIVE', 54),
(70, 2, 3, 'UG Farm 070', 'Düsseldorf', 429.0, 'ACTIVE', 25),
(71, 2, 2, 'UG Farm 071', 'Berlin', 298.0, 'ACTIVE', 32),
(72, 1, 1, 'UG Farm 072', 'Munich', 322.0, 'ACTIVE', 60),
(73, 1, 3, 'UG Farm 073', 'Hamburg', 337.0, 'ACTIVE', 20),
(74, 2, 1, 'UG Farm 074', 'Frankfurt', 471.0, 'ACTIVE', 26),
(75, 2, 3, 'UG Farm 075', 'Cologne', 114.0, 'ACTIVE', 69);

SELECT setval(
    'farms_id_seq',
    (SELECT MAX(id) FROM farms)
);

INSERT INTO crop_categories (
    id,
    name,
    description 
)
VALUES
(1, 'Leafy Greens', 'Fast-growing vegetables valued for their edible leaves, typically harvested young for optimal tenderness and flavor'),
(2, 'Herbs', 'Aromatic plants used for flavoring, garnishing, or medicinal purposes, often requiring specific growing conditions for optimal oil content'),
(3, 'Microgreens', 'Young vegetable greens harvested 1-3 weeks after germination, prized for intense flavor and high nutrient density'),
(4, 'Specialty Crops', 'Unique, premium produce such as edible flowers and baby bok choy, cultivated to meet niche market demands and offer higher profit margins.');

SELECT setval(
    'crop_categories_id_seq',
    (SELECT MAX(id) FROM crop_categories)
);

INSERT INTO crops (
    id,
    category_id,
    name,
    description  
)
VALUES
(1, 2, 'Basil', 'Aromatic herb used in Mediterranean cuisine'),
(2, 2, 'Mint', 'Refreshing herb used in drinks and culinary dishes'),
(3, 2, 'Parsley', 'Versatile herb for garnish and flavoring'),
(4, 2, 'Cilantro', 'Herb with citrusy flavor, used fresh in various dishes'),
(5, 2, 'Thyme', 'Small-leaved herb, widely used in cooking'),
(6, 2, 'Rosemary', 'Fragrant, woody herb used in roasting and baking'),

(7, 1, 'Romaine Lettuce', 'Crisp, elongated leaves with a slightly sweet flavor, often used in salads and wraps'),
(8, 1, 'Butterhead Lettuce', 'Soft, tender leaves with a mild, buttery taste, prized for its delicate texture'),
(9, 1, 'Arugula Lettuce', 'Peppery, tangy green that adds a bold flavor to salads and sandwiches'),
(10, 1, 'Spinach', 'Tender, nutrient-rich green often used fresh or cooked'),
(11, 1, 'Kale', 'Leafy green with high vitamin content, often cooked or eaten raw'),
(12, 1, 'Swiss Chard', 'Leafy green with colorful stems, versatile in cooking'),

(13, 3, 'Radish', 'Spicy, crisp microgreens with vibrant stems and leaves, adding color and bite to dishes'),
(14, 3, 'Pea Shoots', 'Tender, sweet shoots with a fresh pea flavor, commonly used in salads and garnishes'),
(15, 3, 'Sunflower', 'Crunchy, nutty-flavored microgreens rich in protein and texture'),
(16, 3, 'Broccoli', 'Mild, nutrient-dense greens prized for their delicate flavor and high vitamin content'),

(17, 4, 'Nasturtium', 'Vibrant edible flowers with a peppery flavor, used for garnishing and adding color to dishes'),
(18, 4, 'Viola', 'Delicate edible blooms with a mild, floral taste, often used in salads and desserts for visual appeal'),
(19, 4, 'Baby Bok Choy', 'Tender, compact variety of bok choy with mild flavor and crisp texture, ideal for stir-fries and sautéed dishes');

SELECT setval(
    'crops_id_seq',
    (SELECT MAX(id) FROM crops)
);

COPY harvests (
    farm_id,
    crop_id,
    weight_kg,
    quality_grade_id,
    created_at,
    updated_at    
)
FROM PROGRAM 'gunzip -c /data/harvests.csv.gz'
WITH (
    FORMAT csv,
    HEADER true,
    NULL ''
);
select setval(
    'harvests_id_seq',
    (SELECT MAX(id) FROM harvests)
);

INSERT INTO sensors (
    farm_id,
    sensor_type_id,
    serial_number,
    status,
    installed_at
)
SELECT
    f.id,
    s.id,
    CONCAT(
        CASE s.id
            WHEN 1 THEN 'TEMP-20240315-'
            WHEN 2 THEN 'HUM-20240322-'
            WHEN 3 THEN 'LIGHT-20240320-'
            WHEN 4 THEN 'PH-20240318-'
            WHEN 5 THEN 'ENER-20240325-'
            WHEN 6 THEN 'CO2-20240319-'
        END,
        LPAD(ROW_NUMBER() OVER (ORDER BY f.id, s.id)::text, 3, '0')
    ),
    'ACTIVE',
    1749350000
FROM farms f
CROSS JOIN sensor_types s;

INSERT INTO farm_crops (
    farm_id,
    crop_id,
    started_at,
    ended_at
)
SELECT
    f.id,
    c.id,
    1749350000,
    NULL
FROM farms f
CROSS JOIN crops c;
