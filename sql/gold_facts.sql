-- P27 — gold fact: one row per product, is_outlier filled by the
-- pipeline (per-category IQR fences need quartiles SQLite cannot
-- compute); default 0 here.
DROP TABLE IF EXISTS fact_catalogue;
CREATE TABLE fact_catalogue AS
SELECT product_id, category, brand, price_usd, rating_stars,
       review_count, screen_inches, ram_gb, storage_gb, price_band, 0 AS is_outlier
FROM silver_catalogue;
