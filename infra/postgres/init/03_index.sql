CREATE INDEX idx_harvests_farm_id
ON harvests(farm_id);

CREATE INDEX idx_harvests_crop_id
ON harvests(crop_id);

CREATE INDEX idx_harvests_updated_at
ON harvests(updated_at);