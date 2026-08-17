# Query conventions

Rules that span more than one table. Anything that describes a single table or
a single column belongs in the DDL instead, as a `COMMENT`, where it cannot
drift from the object it describes; the schema resource renders those comments
along with the rest of the DDL. Read the schema resource, or call
`describe_table`, before writing SQL - this file only covers what a comment on
one object cannot express.

## 1. Attributing a fact to the version that was valid at the time

The historical dimensions keep one row per version of an entity. A fact points
at the entity, not at a version, so the join has to select the version whose
validity window contains the event:

```sql
SELECT h.harvest_id, h.weight_kg, f.name, f.city
FROM fact_harvests AS h FINAL
INNER JOIN (SELECT * FROM dim_farm FINAL) f
    ON  h.farm_id = f.farm_id
    AND h.harvested_at >= f.valid_from
    AND h.harvested_at <  f.valid_to
```

Without the window the join multiplies rows as soon as a farm has a second
version. For a question about the present, filter `is_current = 1` instead of
carrying the window.

## 2. Join facts to dimensions on `*_id`, never on `*_key`

A `*_key` is a surrogate generated per version; a `*_id` is the id the source
system uses. A fact carries the surrogate of the version valid at load time, so
joining on it silently drops rows once the dimension gains a version.

The calendars are the exception: `date_key` and `time_key` are stable
identifiers rather than surrogates, and are the correct join columns for
`dim_date` and `dim_time`.

## 3. Latest reading per sensor

The live values on a dashboard are the newest reading per sensor type, which is
`argMax` over the timestamp - not `max(value)`, which returns the largest
reading ever taken:

```sql
SELECT
    sensor_type_id,
    argMax(value, reading_ts) AS latest_value,
    max(reading_ts)           AS reading_ts
FROM fact_sensor_readings FINAL
WHERE farm_id = 1
GROUP BY sensor_type_id
```

## 4. Sensor type ids

Stable across the warehouse, so filtering on `sensor_type_id` needs no join:

| `sensor_type_id` | Name |
| --- | --- |
| 1 | Temperature |
| 2 | Humidity |
| 3 | Light Intensity |
| 4 | pH Level |
| 5 | Energy Usage |
| 6 | CO2 Concentration |

The optimal range per type is versioned on `dim_sensor_type` and changes over
time, so read it from there rather than assuming a fixed range.
