-- t08: every silver row carries one of the five price bands.
SELECT product_id, price_band
FROM silver_catalogue
WHERE price_band NOT IN ('Under $300', '$300 - $599', '$600 - $999',
                         '$1000 - $1499', '$1500+');
