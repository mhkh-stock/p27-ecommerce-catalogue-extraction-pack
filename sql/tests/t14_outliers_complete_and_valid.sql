-- t14: every fact row priced above its category upper fence must be
-- in mart_price_outliers, and every mart row must be above its fence.
SELECT f.product_id
FROM fact_catalogue f
WHERE f.price_usd > (SELECT MAX(upper_fence_usd) FROM mart_price_outliers
                     WHERE category = f.category)
  AND f.product_id NOT IN (SELECT product_id FROM mart_price_outliers)
UNION ALL
SELECT product_id FROM mart_price_outliers WHERE price_usd <= upper_fence_usd;
