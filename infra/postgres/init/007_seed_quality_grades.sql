INSERT INTO quality_grades (
    code,
    name,
    description
)
VALUES
(
    'A',
    'Premium',
    'Highest quality produce with perfect appearance, optimal size, and superior taste - suitable for high-end retail and restaurants'
),
(
    'B',
    'Standard',
    'Good quality produce with minor cosmetic imperfections but excellent nutritional value - ideal for general retail markets'
),
(
    'C',
    'Commercial',
    'Acceptable quality with noticeable cosmetic flaws but good nutritional content - suitable for food service and wholesale'
),
(
    'D',
    'Processing',
    'Lower grade produce with significant cosmetic issues but safe for consumption - used for processed foods, juices, and sauces'
),
(
    'E',
    'Livestock Feed',
    'Produce not suitable for human consumption due to quality issues - repurposed as animal feed or compost material'
)
ON CONFLICT (code) DO NOTHING;