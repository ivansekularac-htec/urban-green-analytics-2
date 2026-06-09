-- =========================
-- ENUMS
-- =========================

CREATE TYPE farm_status AS ENUM (
    'ACTIVE',
    'MAINTENANCE',
    'INACTIVE'
);

CREATE TYPE sensor_status AS ENUM (
    'ACTIVE',
    'OFFLINE',
    'MAINTENANCE'
);

-- =========================
-- LOOKUP TABLES
-- =========================

CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE quality_grades (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE farm_infrastructure_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE growing_system_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE crop_categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE sensor_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    unit VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    optimal_min DECIMAL(10,3),
    optimal_max DECIMAL(10,3),
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

-- =========================
-- MAIN TABLES
-- =========================

CREATE TABLE farms (
    id BIGSERIAL PRIMARY KEY,
    infrastructure_type_id BIGINT NOT NULL,
    growing_system_type_id BIGINT NOT NULL,

    name VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    size_m2 decimal(10,3),
    status farm_status NOT NULL DEFAULT 'ACTIVE',
    growing_beds_count INTEGER,

    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_farms_infrastructure_type
        FOREIGN KEY (infrastructure_type_id)
        REFERENCES farm_infrastructure_types(id),

    CONSTRAINT fk_farms_growing_system_type
        FOREIGN KEY (growing_system_type_id)
        REFERENCES growing_system_types(id)
);

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,

    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_ACTIVE BOOLEAN NOT NULL DEFAULT TRUE,

    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)
);

CREATE TABLE crops (
    id BIGSERIAL PRIMARY KEY,

    category_id BIGINT NOT NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),

    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_crop_category
        FOREIGN KEY (category_id)
        REFERENCES crop_categories(id)
);

-- =========================
-- MANY-TO-MANY TABLES
-- =========================

CREATE TABLE user_roles (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    farm_id BIGINT,

    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_user_roles_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_roles_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id),

    CONSTRAINT fk_user_roles_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_user_role_farm
        UNIQUE(user_id, role_id, farm_id)
);

CREATE TABLE farm_crops (
    id BIGSERIAL PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,

    started_at BIGINT NOT NULL,
    ended_at BIGINT,

    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_farm_crops_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_farm_crops_crop
        FOREIGN KEY (crop_id)
        REFERENCES crops(id)
        ON DELETE CASCADE
);

-- =========================
-- SENSORS
-- =========================

CREATE TABLE sensors (
    id BIGSERIAL PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    sensor_type_id BIGINT NOT NULL,

    serial_number VARCHAR(255) NOT NULL UNIQUE,
    status sensor_status NOT NULL DEFAULT 'ACTIVE',
    installed_at BIGINT,

    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_sensor_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_sensor_type
        FOREIGN KEY (sensor_type_id)
        REFERENCES sensor_types(id)
);

-- =========================
-- HARVESTS
-- =========================

CREATE TABLE harvests (
    id BIGSERIAL PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,
    quality_grade_id BIGINT,

    weight_kg DECIMAL(10,3) NOT NULL,

    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),
    updated_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT),

    CONSTRAINT fk_harvest_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id),

    CONSTRAINT fk_harvest_crop
        FOREIGN KEY (crop_id)
        REFERENCES crops(id),

    CONSTRAINT fk_harvest_quality_grade
        FOREIGN KEY (quality_grade_id)
        REFERENCES quality_grades(id)
);

-- =========================
-- INDEXES
-- =========================


CREATE INDEX idx_harvests_farm
    ON harvests(farm_id, updated_at DESC);
