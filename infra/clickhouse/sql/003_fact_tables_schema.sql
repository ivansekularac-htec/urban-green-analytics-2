CREATE TABLE [IF NOT EXIST] [db.]fact_harvest
(
    harvest_key UInt32 [PRIMARY KEY],
    harvest_id UInt32,

    date_key UInt32,
    harvest_timestamp DateTime,

    weight Float32,

    quality_grade_key UInt32,
    crop_key UInt32,
    farm_key UInt32,
    loaded_at DateTime
)

CREATE TABLE [IF NOT EXIST] [db.]fact_sensor_reading 
(
    sensor_reading_key UInt32 [PRIMARY KEY],
    sensor_reading_id UInt32,

    date_key UInt32,
    timestamp DateTime,

    value Float32,

    sensor_key UInt32,
    farm_key UInt32,
    loaded_at DateTime
)