USE urbangreen;

CREATE TABLE IF NOT EXISTS fact_harvest
(
    harvest_key UInt32,
    harvest_id UInt32,

    date_key UInt32,
    event_date Date,
    timestamp DateTime,

    weight Float32,

    quality_grade_key UInt32,
    crop_key UInt32,
    farm_key UInt32,
    loaded_at DateTime
) ENGINE = MergeTree() -- or ReplacingMergeTree if harvests can be corrected
PARTITION BY toYYYYMM(event_date)
ORDER BY (farm_key, timestamp);

CREATE TABLE IF NOT EXISTS fact_sensor_reading 
(
    sensor_reading_key UInt32,
    sensor_reading_id UInt32,

    date_key UInt32,
    event_date Date,
    timestamp DateTime,

    value Float32,

    sensor_key UInt32,
    farm_key UInt32,
    loaded_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (sensor_key, timestamp);