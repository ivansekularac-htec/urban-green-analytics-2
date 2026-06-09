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