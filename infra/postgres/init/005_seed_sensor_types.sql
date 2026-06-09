INSERT INTO urbangreen.sensor_types (
    name,
    unit,
    description,
    optimal_min,
    optimal_max
)
VALUES
(
    'Temperature',
    '°C',
    'Ambient temperature measurement',
    18,
    25
),
(
    'Humidity',
    '%',
    'Relative humidity percentage',
    50,
    70
),
(
    'Light Intensity',
    'PPFD',
    'Photosynthetic photon flux density',
    200,
    800
),
(
    'pH Level',
    'pH',
    'Acidity/alkalinity of water or soil',
    5,
    7
),
(
    'Energy Usage',
    'kWh',
    'Total electrical energy consumed by the system',
    1,
    1000000
),
(
    'CO2 Concentration',
    'ppm',
    'Carbon dioxide parts per million',
    400,
    1200
)
ON CONFLICT (name) DO NOTHING;