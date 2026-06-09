CREATE TABLE farm_import (
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

CREATE TABLE crop_import (
    crop_id INTEGER,
    crop_name VARCHAR(100),
    crop_category VARCHAR(100),
    description VARCHAR(500)
);

COPY crop_import
FROM '/data/crops.csv'
DELIMITER ','
CSV HEADER;