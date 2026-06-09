INSERT INTO urbangreen.infrastructure_types (
    name,
    description
)
VALUES
(
    'Hydroponic',
    'Soilless growing system where plants receive nutrients through mineral-rich water solutions in controlled environments'
),
(
    'Aeroponic',
    'Integrated system combining fish farming with plant cultivation, where fish waste provides nutrients for plants'
)
ON CONFLICT (name) DO NOTHING;