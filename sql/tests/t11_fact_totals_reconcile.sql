-- t11: fact count and price sum must equal silver exactly.
SELECT 'count mismatch' AS violation
WHERE (SELECT COUNT(*) FROM fact_catalogue) <> (SELECT COUNT(*) FROM silver_catalogue)
UNION ALL
SELECT 'sum mismatch' AS violation
WHERE ABS((SELECT SUM(price_usd) FROM fact_catalogue)
        - (SELECT SUM(price_usd) FROM silver_catalogue)) > 0.01;
