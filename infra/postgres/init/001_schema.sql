CREATE SCHEMA IF NOT EXISTS urbangreen;

CREATE TABLE urbangreen.users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
);

CREATE TABLE urbangreen.roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
);

CREATE TABLE urbangreen.infrastructure_types (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
);

CREATE TABLE urbangreen.growing_system_types (
     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     name VARCHAR(100) NOT NULL UNIQUE,
     description VARCHAR(500),
     created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
     updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
);

CREATE TABLE urbangreen.sensor_types (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    unit VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    optimal_min DECIMAL(10,3),
    optimal_max DECIMAL(10,3),
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
);

CREATE TABLE urbangreen.crop_categories (
     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     name VARCHAR(100) NOT NULL UNIQUE,
     description VARCHAR(500),
     created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
     updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
);

CREATE TABLE urbangreen.quality_grades (
     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     code VARCHAR(100) NOT NULL UNIQUE,
     name VARCHAR(100) NOT NULL,
     description VARCHAR(500),
     created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
     updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT
);

CREATE TYPE urbangreen.farm_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'MAINTENANCE'
);

CREATE TABLE urbangreen.farms (
     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     infrastructure_type_id BIGINT NOT NULL,
     growing_system_type_id BIGINT NOT NULL,
     name VARCHAR(100) NOT NULL UNIQUE,
     city VARCHAR(100) NOT NULL,
     size_m2 DECIMAL(10,3) NOT NULL,
     status urbangreen.farm_status NOT NULL,
     growing_beds_count INTEGER NOT NULL,
     created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
     updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,

     CONSTRAINT fk_farm_infrastructure_type
        FOREIGN KEY (infrastructure_type_id)
        REFERENCES urbangreen.infrastructure_types(id),

     CONSTRAINT fk_farm_growing_system_type
        FOREIGN KEY (growing_system_type_id)
        REFERENCES urbangreen.growing_system_types(id)
);

CREATE TABLE urbangreen.user_roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    farm_id BIGINT,
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,

    CONSTRAINT fk_user_role_user
        FOREIGN KEY (user_id)
        REFERENCES urbangreen.users(id),

    CONSTRAINT fk_user_role_role
        FOREIGN KEY (role_id)
        REFERENCES urbangreen.roles(id),

    CONSTRAINT fk_user_role_farm
        FOREIGN KEY (farm_id)
        REFERENCES urbangreen.farms(id)
);

CREATE TYPE urbangreen.sensor_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'MAINTENANCE'
);

CREATE TABLE urbangreen.sensors (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    farm_id BIGINT NOT NULL,
    sensor_type_id BIGINT NOT NULL,
    serial_number VARCHAR(255) NOT NULL UNIQUE,
    status urbangreen.sensor_status NOT NULL,
    installed_at BIGINT,
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,

    CONSTRAINT fk_sensor_farm
        FOREIGN KEY (farm_id)
        REFERENCES urbangreen.farms(id),

    CONSTRAINT fk_sensor_sensor_type
        FOREIGN KEY (sensor_type_id)
        REFERENCES urbangreen.sensor_types(id)
);

CREATE TABLE urbangreen.crops (
     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     category_id BIGINT NOT NULL,
     name VARCHAR(100) NOT NULL UNIQUE,
     description VARCHAR(500),
     created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
     updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,

     CONSTRAINT fk_crop_category
        FOREIGN KEY (category_id)
        REFERENCES urbangreen.crop_categories(id)
);

CREATE TABLE urbangreen.farm_crops (
     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     farm_id BIGINT NOT NULL,
     crop_id BIGINT NOT NULL,
     started_at BIGINT NOT NULL,
     ended_at BIGINT,
     created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
     updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,

     CONSTRAINT fk_farm_crops_farm
        FOREIGN KEY (farm_id)
        REFERENCES urbangreen.farms(id),

     CONSTRAINT fk_farm_crops_crop
        FOREIGN KEY (crop_id)
        REFERENCES urbangreen.crops(id),

     CONSTRAINT uq_farm_crop
        UNIQUE (farm_id, crop_id)
);

CREATE TABLE urbangreen.harvests (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,
    quality_grade_id BIGINT NOT NULL,
    weight_kg DECIMAL(10,2) NOT NULL,
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT,

    CONSTRAINT fk_harvest_farm
        FOREIGN KEY (farm_id)
        REFERENCES urbangreen.farms(id),

    CONSTRAINT fk_harvest_crop
        FOREIGN KEY (crop_id)
        REFERENCES urbangreen.crops(id),

    CONSTRAINT fk_harvest_quality_grade
        FOREIGN KEY (quality_grade_id)
        REFERENCES urbangreen.quality_grades(id)
);

CREATE INDEX idx_harvests_farm_id
    ON urbangreen.harvests(farm_id);

CREATE INDEX idx_harvests_crop_id
    ON urbangreen.harvests(crop_id);

CREATE INDEX idx_harvests_updated_at
    ON urbangreen.harvests(updated_at);

