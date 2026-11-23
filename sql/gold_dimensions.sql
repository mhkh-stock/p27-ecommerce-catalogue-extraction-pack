-- P27 — gold dimensions: category and brand counts from silver.
DROP TABLE IF EXISTS dim_category;
CREATE TABLE dim_category AS
SELECT category, COUNT(*) AS products
FROM silver_catalogue GROUP BY category;

DROP TABLE IF EXISTS dim_brand;
CREATE TABLE dim_brand AS
SELECT brand, COUNT(*) AS products
FROM silver_catalogue GROUP BY brand;
