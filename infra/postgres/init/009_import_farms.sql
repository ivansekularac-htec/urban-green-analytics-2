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
    infrastructure_types.id,
    growing_system_types.id,
    farm_import.name,
    farm_import.city,
    farm_import.size_m2,
    'ACTIVE',
    farm_import.growing_beds_count
FROM farm_import
JOIN infrastructure_types
    ON infrastructure_types.name = farm_import.infrastructure_type
JOIN growing_system_types
    ON growing_system_types.name = farm_import.growing_system_type;