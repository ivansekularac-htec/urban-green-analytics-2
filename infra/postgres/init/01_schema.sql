CREATE TYPE farm_status AS ENUM (
    'active',
    'maintenance',
    'inactive'
);

CREATE TYPE sensor_status AS ENUM (
    'active',
    'maintenance',
    'inactive'
);
CREATE TABLE roles (
    id BIGINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT,
    updated_at BIGINT
);
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at BIGINT,
    updated_at BIGINT
);
CREATE TABLE quality_grades (
    id BIGINT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    created_at BIGINT,
    updated_at BIGINT
);
CREATE TABLE farm_infrastructure_types (
    id BIGINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT,
    updated_at BIGINT
);
CREATE TABLE growing_system_types (
    id BIGINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT,
    updated_at BIGINT
);
CREATE TABLE crop_categories (
    id BIGINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT,
    updated_at BIGINT
);
CREATE TABLE sensor_types (
    id BIGINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    unit VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    optimal_min DECIMAL(15, 5),
    optimal_max DECIMAL(15, 5),
    created_at BIGINT,
    updated_at BIGINT
);
CREATE TABLE farms (
    id BIGINT PRIMARY KEY,

    infrastructure_type_id BIGINT NOT NULL,
    growing_system_type_id BIGINT NOT NULL,

    name VARCHAR(50) NOT NULL UNIQUE,
    city VARCHAR(50) NOT NULL,

    size_m2 DECIMAL(10, 3) NOT NULL,

    status farm_status NOT NULL,

    growing_beds_count INTEGER NOT NULL,

    created_at BIGINT,
    updated_at BIGINT,

    CONSTRAINT fk_farms_infrastructure_type
        FOREIGN KEY (infrastructure_type_id)
        REFERENCES farm_infrastructure_types(id),

    CONSTRAINT fk_farms_growing_system_type
        FOREIGN KEY (growing_system_type_id)
        REFERENCES growing_system_types(id)
);
CREATE TABLE crops (
    id BIGINT PRIMARY KEY,

    category_id BIGINT NOT NULL,

    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),

    created_at BIGINT,
    updated_at BIGINT,

    CONSTRAINT fk_crops_category
        FOREIGN KEY (category_id)
        REFERENCES crop_categories(id)
);
CREATE TABLE user_roles (
    id BIGINT PRIMARY KEY,

    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    farm_id BIGINT,

    created_at BIGINT,
    updated_at BIGINT,

    CONSTRAINT fk_user_roles_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),

    CONSTRAINT fk_user_roles_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id),

    CONSTRAINT fk_user_roles_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id),

    CONSTRAINT uq_user_roles
        UNIQUE (user_id, role_id, farm_id)
);
CREATE TABLE farm_crops (
    id BIGINT PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,

    started_at BIGINT NOT NULL,
    ended_at BIGINT,

    created_at BIGINT,
    updated_at BIGINT,

    CONSTRAINT fk_farm_crops_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id),

    CONSTRAINT fk_farm_crops_crop
        FOREIGN KEY (crop_id)
        REFERENCES crops(id),

    CONSTRAINT uq_farm_crops
        UNIQUE (farm_id, crop_id, started_at)
);

CREATE TABLE sensors (
    id BIGINT PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    sensor_type_id BIGINT NOT NULL,

    serial_number VARCHAR(255) NOT NULL UNIQUE,

    status sensor_status NOT NULL,

    installed_at BIGINT,

    created_at BIGINT,
    updated_at BIGINT,

    CONSTRAINT fk_sensors_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id),

    CONSTRAINT fk_sensors_sensor_type
        FOREIGN KEY (sensor_type_id)
        REFERENCES sensor_types(id)
);
CREATE TABLE harvests (
    id BIGINT PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,
    quality_grade_id BIGINT NOT NULL,

    weight_kg DECIMAL(10, 3) NOT NULL,

    created_at BIGINT,
    updated_at BIGINT,

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

CREATE INDEX idx_harvests_created_at 
ON harvests (created_at);

CREATE INDEX idx_harvests_updated_at 
ON harvests (updated_at);