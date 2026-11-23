-- t04: rating stars are whole stars 1-5.
SELECT product_id, rating_stars
FROM bronze_catalogue
WHERE CAST(rating_stars AS INTEGER) NOT BETWEEN 1 AND 5
   OR rating_stars NOT GLOB '[0-9]';
