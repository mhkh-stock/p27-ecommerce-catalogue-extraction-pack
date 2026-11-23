-- t01: bronze must hold exactly the rows in the raw CSV (147).
SELECT 'row count mismatch' AS violation
WHERE (SELECT COUNT(*) FROM bronze_catalogue) <> 147;
