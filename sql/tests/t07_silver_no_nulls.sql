-- t07: silver must have no NULL price, brand, category or title.
SELECT product_id
FROM silver_catalogue
WHERE price_usd IS NULL OR brand IS NULL OR brand = ''
   OR category IS NULL OR title IS NULL OR title = '';
