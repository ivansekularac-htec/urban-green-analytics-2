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