-- t02: one listing per product_id in bronze.
SELECT product_id, COUNT(*) AS n
FROM bronze_catalogue GROUP BY product_id HAVING n > 1;
