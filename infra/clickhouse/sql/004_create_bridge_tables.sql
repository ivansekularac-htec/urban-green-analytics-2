USE urbangreen;

CREATE TABLE IF NOT EXISTS bridge_user_role 
(
    user_key UInt32,
    farm_key UInt32,

    role_id UInt32,
    role_name String,
    role_description String,

    valid_from DateTime,
    valid_to DateTime,
    is_current Bool,
    loaded_at DateTime
) ENGINE = MergeTree()
ORDER BY(user_key, farm_key, role_id);