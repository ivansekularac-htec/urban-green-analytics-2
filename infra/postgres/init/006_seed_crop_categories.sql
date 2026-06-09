INSERT INTO urbangreen.crop_categories (
    name,
    description
)
VALUES
(
    'Leafy Greens',
    'Fast-growing vegetables valued for their edible leaves, typically harvested young for optimal tenderness and flavor'
),
(
    'Herbs',
    'Aromatic plants used for flavoring, garnishing, or medicinal purposes, often requiring specific growing conditions for optimal oil content'
),
(
    'Microgreens',
    'Young vegetable greens harvested 1-3 weeks after germination, prized for intense flavor and high nutrient density'
),
(
    'Specialty Crops',
    'Unique, premium produce such as edible flowers and baby bok choy, cultivated to meet niche market demands and offer higher profit margins.'
)
ON CONFLICT (name) DO NOTHING;