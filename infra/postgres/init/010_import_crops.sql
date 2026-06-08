INSERT INTO crops (
    category_id,
    name,
    description
)
SELECT
    cc.id,
    ci.crop_name,
    ci.description
FROM crop_import ci
JOIN crop_categories cc
    ON cc.name = ci.crop_category;