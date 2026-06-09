-- FARMS

CREATE TYPE farm_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'MAINTENANCE'
);

CREATE TABLE infrastructure_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT)
);

CREATE TABLE growing_system_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT)
);

CREATE TABLE farms (
    id BIGSERIAL PRIMARY KEY,
    infrastructure_type_id BIGINT NOT NULL,
    growing_system_type_id BIGINT NOT NULL,

    name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,

    size_m2 DECIMAL(10,3) NOT NULL,
    status farm_status NOT NULL,

    growing_beds_count INTEGER NOT NULL,

    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    
    CONSTRAINT fk_farm_infrastructure
        FOREIGN KEY (infrastructure_type_id)
        REFERENCES infrastructure_types(id),

    CONSTRAINT fk_farm_growing_system
        FOREIGN KEY (growing_system_type_id)
        REFERENCES growing_system_types(id)
);

-- USERS AND ROLES

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT)
);

CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT)
);

CREATE TABLE user_roles (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    farm_id BIGINT,

    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),

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


-- CROPS

CREATE TABLE crop_categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT)
);

CREATE TABLE crops (
    id BIGSERIAL PRIMARY KEY,

    category_id BIGINT NOT NULL,

    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(255),

    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),

    CONSTRAINT fk_crop_category
        FOREIGN KEY (category_id)
        REFERENCES crop_categories(id)
);

CREATE TABLE farm_crops (
    id BIGSERIAL PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,

    started_at BIGINT NOT NULL,
    ended_at BIGINT,

    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),

   	CONSTRAINT fk_farm_crops_farm
	    FOREIGN KEY (farm_id)
	    REFERENCES farms(id),
	
	CONSTRAINT fk_farm_crops_crop
	    FOREIGN KEY (crop_id)
	    REFERENCES crops(id)
);


-- HARVESTS

CREATE TABLE quality_grades (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT)
);

CREATE TABLE harvests (
    id BIGSERIAL PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    crop_id BIGINT NOT NULL,
    quality_grade_id BIGINT NOT NULL,

    weight_kg DECIMAL(10,3) NOT NULL,

    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),

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


-- SENSORS

CREATE TYPE sensor_status AS ENUM (
    'ACTIVE',
    'OFFLINE',
    'FAULTY'
);

CREATE TABLE sensor_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    unit VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    optimal_min NUMERIC(12, 5),
    optimal_max NUMERIC(12, 5),
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT)
);

CREATE TABLE sensors (
    id BIGSERIAL PRIMARY KEY,

    farm_id BIGINT NOT NULL,
    sensor_type_id BIGINT NOT NULL,

    serial_number VARCHAR(255) NOT NULL UNIQUE,

    status sensor_status NOT NULL,

    installed_at BIGINT,
    created_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),
    updated_at BIGINT NOT NULL DEFAULT CAST(EXTRACT(EPOCH FROM NOW()) AS BIGINT),

	CONSTRAINT fk_sensors_farm
	    FOREIGN KEY (farm_id)
	    REFERENCES farms(id),
	
	CONSTRAINT fk_sensors_sensor_type
	    FOREIGN KEY (sensor_type_id)
	    REFERENCES sensor_types(id)
);