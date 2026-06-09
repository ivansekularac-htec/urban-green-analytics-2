CREATE SCHEMA IF NOT EXISTS app;
SET search_path TO app;

CREATE TYPE FARM_STATUS AS ENUM (
    'active',
    'maintenance',
    'inactive'
);

CREATE TYPE SENSOR_STATUS AS ENUM (
    'active',
    'offline',
    'maintenance'
);

CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE quality_grades (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description VARCHAR,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE farm_infrastructure_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE growing_system_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE crop_categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE sensor_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR,
    unit VARCHAR(100) NOT NULL,
    optimal_min DECIMAL(15, 5),
    optimal_max DECIMAL(15, 5),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE farms (
    id BIGSERIAL PRIMARY KEY,
    infrastructure_type_id BIGINT NOT NULL,
    growing_system_type_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    size_m2 DECIMAL(10, 3) NOT NULL,
    status FARM_STATUS NOT NULL,
    growing_beds_count INTEGER NOT NULL,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_farms_infrastructure_type
        FOREIGN KEY (infrastructure_type_id)
        REFERENCES farm_infrastructure_types(id),

    CONSTRAINT fk_farms_growing_system_type
        FOREIGN KEY (growing_system_type_id)
        REFERENCES growing_system_types(id)
);

CREATE TABLE user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    farm_id BIGINT,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_user_roles_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),

    CONSTRAINT fk_user_roles_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id),

    CONSTRAINT fk_user_roles_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id)
);

CREATE TABLE crops (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_crops_category
        FOREIGN KEY (category_id)
        REFERENCES crop_categories(id)
);

CREATE TABLE farm_crops (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,
    started_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    ended_at BIGINT,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_farm_crops_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id),

    CONSTRAINT fk_farm_crops_crop
        FOREIGN KEY (crop_id)
        REFERENCES crops(id)
);

CREATE TABLE sensors (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL,
    sensor_type_id BIGINT NOT NULL,
    serial_number VARCHAR(255) NOT NULL UNIQUE,
    status SENSOR_STATUS NOT NULL,
    installed_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_sensors_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id),

    CONSTRAINT fk_sensors_sensor_type
        FOREIGN KEY (sensor_type_id)
        REFERENCES sensor_types(id)
);

CREATE TABLE harvests (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,
    quality_grade_id BIGINT NOT NULL,
    weight_kg DECIMAL(10, 3) NOT NULL,
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_harvests_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id),

    CONSTRAINT fk_harvests_crop
        FOREIGN KEY (crop_id)
        REFERENCES crops(id),

    CONSTRAINT fk_harvests_quality_grade
        FOREIGN KEY (quality_grade_id)
        REFERENCES quality_grades(id)
);

ALTER TABLE user_roles
ADD CONSTRAINT uq_user_roles_user_role_farm
UNIQUE (user_id, role_id, farm_id);

ALTER TABLE farm_crops
ADD CONSTRAINT uq_farm_crops_farm_crop_started_at
UNIQUE (farm_id, crop_id, started_at);

-- Indexes

CREATE INDEX idx_harvests_updated_at
    ON harvests (updated_at);

CREATE INDEX idx_harvests_farm_id
    ON harvests (farm_id);

CREATE INDEX idx_sensors_farm_id_status
    ON sensors (farm_id, status);
