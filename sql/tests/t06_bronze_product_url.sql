-- t06: every product URL points at the site's product page.
SELECT product_id, product_url
FROM bronze_catalogue
WHERE product_url NOT LIKE 'https://webscraper.io/test-sites/e-commerce/allinone/product/%';
