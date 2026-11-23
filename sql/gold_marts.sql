-- P27 — gold marts. Medians and outlier fences are computed in
-- Python (src/build_pipeline.py) and UPDATEed in after this file
-- runs; the mean/median columns start at 0.0 and must not be read
-- before the pipeline finishes.
DROP TABLE IF EXISTS mart_price_by_category;
CREATE TABLE mart_price_by_category AS
SELECT category,
       COUNT(*) AS products,
       MIN(price_usd) AS min_price_usd,
       MAX(price_usd) AS max_price_usd,
       ROUND(AVG(price_usd), 2) AS mean_price_usd,
       0.0 AS median_price_usd,
       ROUND(SUM(price_usd), 2) AS total_value_usd
FROM silver_catalogue GROUP BY category;

DROP TABLE IF EXISTS mart_price_by_brand;
CREATE TABLE mart_price_by_brand AS
SELECT brand,
       COUNT(*) AS products,
       MIN(price_usd) AS min_price_usd,
       MAX(price_usd) AS max_price_usd,
       ROUND(AVG(price_usd), 2) AS mean_price_usd,
       0.0 AS median_price_usd,
       ROUND(AVG(rating_stars), 2) AS avg_rating,
       SUM(review_count) AS total_reviews
FROM silver_catalogue GROUP BY brand;

DROP TABLE IF EXISTS mart_rating_by_category;
CREATE TABLE mart_rating_by_category AS
SELECT category,
       COUNT(*) AS products,
       ROUND(AVG(rating_stars), 2) AS avg_rating,
       SUM(CASE WHEN rating_stars >= 4 THEN 1 ELSE 0 END) AS rated_4_plus,
       SUM(CASE WHEN rating_stars = 1 THEN 1 ELSE 0 END) AS rated_1,
       SUM(CASE WHEN review_count = 0 THEN 1 ELSE 0 END) AS zero_reviews,
       SUM(review_count) AS total_reviews,
       ROUND(SUM(rating_stars * review_count) * 1.0
             / NULLIF(SUM(review_count), 0), 2) AS weighted_rating
FROM silver_catalogue GROUP BY category;

DROP TABLE IF EXISTS mart_price_bands;
CREATE TABLE mart_price_bands AS
SELECT price_band,
       COUNT(*) AS products,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM silver_catalogue), 2) AS share_pct,
       ROUND(AVG(price_usd), 2) AS avg_price_usd
FROM silver_catalogue GROUP BY price_band;

-- mart_price_outliers and mart_top_reviewed are INSERTed by the
-- pipeline (they need per-category quartiles).
DROP TABLE IF EXISTS mart_price_outliers;
CREATE TABLE mart_price_outliers (
    product_id   TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    category     TEXT NOT NULL,
    brand        TEXT NOT NULL,
    price_usd    REAL NOT NULL,
    q1_usd       REAL NOT NULL,
    q3_usd       REAL NOT NULL,
    upper_fence_usd REAL NOT NULL,
    excess_usd   REAL NOT NULL
);

DROP TABLE IF EXISTS mart_top_reviewed;
CREATE TABLE mart_top_reviewed AS
SELECT product_id, title, category, brand, price_usd, rating_stars, review_count
FROM silver_catalogue
ORDER BY review_count DESC, rating_stars DESC, price_usd ASC
LIMIT 15;
