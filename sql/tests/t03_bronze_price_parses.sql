-- t03: every listed price parses to a positive number.
SELECT product_id, price_usd_raw
FROM bronze_catalogue
WHERE CAST(REPLACE(REPLACE(price_usd_raw, '$', ''), ',', '') AS REAL) IS NULL
   OR CAST(REPLACE(REPLACE(price_usd_raw, '$', ''), ',', '') AS REAL) <= 0;
