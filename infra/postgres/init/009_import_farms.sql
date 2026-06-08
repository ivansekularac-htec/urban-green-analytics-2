INSERT INTO farms (
    infrastructure_type_id,
    growing_system_type_id,
    name,
    city,
    size_m2,
    status,
    growing_beds_count
)
SELECT
    it.id,
    gst.id,
    fi.name,
    fi.city,
    fi.size_m2,
    'ACTIVE',
    fi.growing_beds_count
FROM farm_import fi
JOIN infrastructure_types it
    ON it.name = fi.infrastructure_type
JOIN growing_system_types gst
    ON gst.name = fi.growing_system_type;