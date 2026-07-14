CREATE TABLE [IF NOT EXIST] [db.]dim_date
(
    date_key UInt32 [PRIMARY KEY],
    full_Date Date,

    day UInt8,
    week UInt8,
    month UInt8,
    quarter UInt8,
    year UInt16,

    is_weekend Bool,
    loaded_at DateTime,
)

CREATE TABLE [IF NOT EXIST] [db.]quality_grade
(
    quality_grade_key UInt32 [PRIMARY KEY],
    quality_grade_id UInt32,

    code String,
    name String,
    description String,

    loaded_at DateTime
)

CREATE TABLE [IF NOT EXIST] [db.]dim_crop
(
    crop_key UInt32 [PRIMARY KEY],
    crop_id UInt32,

    name String,
    description String,

    crop_category_id UInt32,
    crop_category_name String,
    crop_category_description String,

    loaded_at DateTime
)

CREATE TABLE [IF NOT EXIST] [db.]dim_farm 
(
    farm_key UInt32 [PRIMARY KEY],
    farm_id UInt32,

    infrastructure_type_id UInt32,
    infrastructure_type_name String,
    infrastructure_type_description String,

    growing_system_type_id UInt32,
    growing_system_type_name String,
    growing_system_type_description String,

    name String,
    city String,

    size_m2 UInt32,
    status farm_status,
    growing_beds_count UInt16,

    valid_from DateTime,
    valid_to DateTime,
    is_current Bool,
    loaded_at DateTime
)

CREATE TABLE [IF NOT EXIST] [db.]dim_sensor
(
    sensor_key UInt32 [PRIMARY KEY],
    sensor_id UInt32,

    sensor_type_key UInt32,
    sensor_type_name String,
    sensor_type_description String,

    sensor_type_optimal_min Float32,
    sensor_type_optimal_max Float32,

    serial_number String,

    status sensor_status,
    installed_at DateTime,

    valid_from DateTime,
    valid_to DateTime,
    is_current Bool,
    loaded_at DateTime
)

CREATE TABLE [IF NOT EXIST] [db.]dim_user
(
    user_key UInt32 [PRIMARY KEY],
    user_id UInt32,

    email String,
    full_name String,

    is_active Bool,
    loaded_at DateTime
)
