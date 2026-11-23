-- t10: fact grain is one row per product_id.
SELECT product_id, COUNT(*) AS n
FROM fact_catalogue GROUP BY product_id HAVING n > 1;
