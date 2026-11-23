-- t05: review counts are non-negative integers.
SELECT product_id, review_count
FROM bronze_catalogue
WHERE CAST(review_count AS INTEGER) < 0
   OR review_count NOT GLOB '[0-9]*';
