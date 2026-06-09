INSERT INTO urbangreen.growing_system_types (
    name,
    description
)
VALUES
(
    'Vertical Farming',
    'Plants grown in vertically stacked layers with artificial LED lighting and precise nutrient delivery systems'
),
(
    'Tower Farming',
    'Cylindrical or tower-shaped growing structures that maximize vertical space while minimizing floor footprint'
),
(
    'Flat Bed Farming',
    'Crops grown on level, flat soil beds allowing uniform irrigation, easy planting, and mechanized field operations'
)
ON CONFLICT (name) DO NOTHING;