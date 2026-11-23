-- t12: mart price-by-category products and totals must equal silver.
SELECT 'products mismatch' AS violation
WHERE (SELECT SUM(products) FROM mart_price_by_category)
   <> (SELECT COUNT(*) FROM silver_catalogue)
UNION ALL
SELECT 'value mismatch' AS violation
WHERE ABS((SELECT SUM(total_value_usd) FROM mart_price_by_category)
        - (SELECT SUM(price_usd) FROM silver_catalogue)) > 0.01;
