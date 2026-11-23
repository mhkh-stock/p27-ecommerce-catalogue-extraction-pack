-- P27 — silver_catalogue: clean the scraped listing into typed values.
--
-- price_usd: strip "$" and commas, cast to REAL.
-- brand: the first word of the title is NOT the brand on this site —
-- sub-brands and model lines sit there instead (ThinkPad, Aspire,
-- Galaxy, Hewlett, Pavilion, ProBook, Inspiron, IdeaTab, iPad,
-- iPhone, Iconia, MeMO). Normalise them to the maker with a CASE map;
-- anything unmapped keeps its first word as-is.
-- price_band: fixed bands a buyer actually shops in.
-- Spec columns (screen_inches, ram_gb, storage_gb, storage_type) are
-- filled by src/build_pipeline.py (SQLite has no regex); this model
-- leaves them NULL and the pipeline UPDATEs them from the description.

DROP TABLE IF EXISTS silver_catalogue;
CREATE TABLE silver_catalogue AS
SELECT
    product_id,
    category,
    title,
    CASE
        WHEN title LIKE 'ThinkPad%' OR title LIKE 'Lenovo%' OR title LIKE 'IdeaTab%' THEN 'Lenovo'
        WHEN title LIKE 'Aspire%' OR title LIKE 'Acer%' OR title LIKE 'Iconia%' THEN 'Acer'
        WHEN title LIKE 'Hewlett%' OR title LIKE 'HP %' OR title LIKE 'Pavilion%' OR title LIKE 'ProBook%' THEN 'HP'
        WHEN title LIKE 'Dell%' OR title LIKE 'Inspiron%' THEN 'Dell'
        WHEN title LIKE 'Apple%' OR title LIKE 'Iphone%' OR title LIKE 'iPad%' THEN 'Apple'
        WHEN title LIKE 'Samsung%' OR title LIKE 'Galaxy%' THEN 'Samsung'
        WHEN title LIKE 'Asus%' OR title LIKE 'MeMO%' OR title LIKE 'MeMo%' OR title LIKE 'Memo%' THEN 'Asus'
        WHEN title LIKE 'Packard%' THEN 'Packard Bell'
        ELSE substr(title, 1, instr(title || ' ', ' ') - 1)
    END AS brand,
    CAST(REPLACE(REPLACE(price_usd_raw, '$', ''), ',', '') AS REAL) AS price_usd,
    CAST(rating_stars AS INTEGER) AS rating_stars,
    CAST(review_count AS INTEGER) AS review_count,
    NULL AS screen_inches,
    NULL AS ram_gb,
    NULL AS storage_gb,
    NULL AS storage_type,
    CASE
        WHEN CAST(REPLACE(REPLACE(price_usd_raw, '$', ''), ',', '') AS REAL) < 300 THEN 'Under $300'
        WHEN CAST(REPLACE(REPLACE(price_usd_raw, '$', ''), ',', '') AS REAL) < 600 THEN '$300 - $599'
        WHEN CAST(REPLACE(REPLACE(price_usd_raw, '$', ''), ',', '') AS REAL) < 1000 THEN '$600 - $999'
        WHEN CAST(REPLACE(REPLACE(price_usd_raw, '$', ''), ',', '') AS REAL) < 1500 THEN '$1000 - $1499'
        ELSE '$1500+'
    END AS price_band,
    CASE WHEN CAST(review_count AS INTEGER) > 0 THEN 1 ELSE 0 END AS has_reviews,
    description,
    product_url
FROM bronze_catalogue;
