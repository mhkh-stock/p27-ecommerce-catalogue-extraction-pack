-- t13: mart rating-by-category review totals must equal silver.
SELECT 'reviews mismatch' AS violation
WHERE (SELECT SUM(total_reviews) FROM mart_rating_by_category)
   <> (SELECT SUM(review_count) FROM silver_catalogue)
UNION ALL
SELECT 'rated_4_plus mismatch' AS violation
WHERE (SELECT SUM(rated_4_plus) FROM mart_rating_by_category)
   <> (SELECT COUNT(*) FROM silver_catalogue WHERE rating_stars >= 4);
