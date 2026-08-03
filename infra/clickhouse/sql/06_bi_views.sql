-- =============================================================================
-- Urban Green Analytics — ClickHouse warehouse init
-- Security entitlements for Superset Row-Level Security
-- =============================================================================
--
-- Purpose:
--   Expose current user→farm grants for Superset RLS.
--   Hides SCD2 (valid_from/valid_to/is_current) behind one stable view.
--
-- Identity contract:
--   username = lower(dim_user.email)
--   Superset Gamma users must be created with that same username (email).
--
-- Admin "see all farms" is NOT modeled here (farm_id = 0 rows are excluded).
-- Superset Admin is exempt from the farm RLS rule instead.
--
-- Dependencies: 02_dimensions_reference.sql (dim_user),
--               03_dimensions_scd.sql (dim_user_farm_role).
-- =============================================================================
USE urbangreen_dw;

CREATE OR REPLACE VIEW v_user_farm_permissions AS
SELECT lower(u.email) AS username, ufr.farm_id AS farm_id
FROM
    dim_user_farm_role AS ufr FINAL
    INNER JOIN dim_user AS u FINAL ON ufr.user_id = u.user_id
WHERE
    ufr.is_current = 1
    AND u.is_active = 1
    AND ufr.farm_id != 0;

-- Helper view that centralizes the high-value crop classification.
CREATE OR REPLACE VIEW bi_crop_classification AS
SELECT
    crop.crop_id,
    crop.name AS crop_name,
    crop.category_name,
    CAST(
        crop.category_name IN (
            'Microgreens',
            'Specialty Crops'
        ),
        'UInt8'
    ) AS is_high_value
FROM dim_crop AS crop FINAL;
