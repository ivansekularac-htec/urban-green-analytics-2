COPY public.harvests (farm_id, crop_id, weight_kg, quality_grade_id, created_at, updated_at)
FROM PROGRAM 'gunzip -c /data/harvests.csv.gz'
WITH (FORMAT csv, HEADER true, NULL '');

-- Reset sequence so new inserts continue after loaded data
SELECT setval('public.harvests_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.harvests));