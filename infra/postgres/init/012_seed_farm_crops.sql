INSERT INTO farm_crops (farm_id, crop_id, started_at)
SELECT
    farms.id,
    crops.id,
    EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
FROM farms
CROSS JOIN crops;