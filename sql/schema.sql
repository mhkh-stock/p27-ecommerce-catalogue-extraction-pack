-- P27 — schema: bronze landing table + gold star-schema DDL.
-- Bronze loads the scraped CSV exactly as listed on the site.
-- Silver cleans it (sql/silver_catalogue.sql); gold is built by
-- sql/gold_dimensions.sql, sql/gold_facts.sql and sql/gold_marts.sql.
-- SQLite. Run via src/build_pipeline.py.

DROP TABLE IF EXISTS bronze_catalogue;
CREATE TABLE bronze_catalogue (
    product_id    TEXT,
    category      TEXT,
    title         TEXT,
    price_usd_raw TEXT,
    rating_stars  TEXT,
    review_count  TEXT,
    description   TEXT,
    product_url   TEXT,
    scraped_at    TEXT
);

-- ---- silver ----
DROP TABLE IF EXISTS silver_catalogue;
CREATE TABLE silver_catalogue (
    product_id    TEXT PRIMARY KEY,
    category      TEXT NOT NULL,
    title         TEXT NOT NULL,
    brand         TEXT NOT NULL,
    price_usd     REAL NOT NULL,
    rating_stars  INTEGER NOT NULL,
    review_count  INTEGER NOT NULL,
    screen_inches REAL,
    ram_gb        INTEGER,
    storage_gb    REAL,
    storage_type  TEXT,
    price_band    TEXT NOT NULL,
    has_reviews   INTEGER NOT NULL,
    description   TEXT NOT NULL,
    product_url   TEXT NOT NULL
);

-- ---- gold star schema ----
DROP TABLE IF EXISTS dim_category;
CREATE TABLE dim_category (
    category TEXT PRIMARY KEY,
    products INTEGER NOT NULL
);

DROP TABLE IF EXISTS dim_brand;
CREATE TABLE dim_brand (
    brand    TEXT PRIMARY KEY,
    products INTEGER NOT NULL
);

DROP TABLE IF EXISTS fact_catalogue;
CREATE TABLE fact_catalogue (
    product_id    TEXT PRIMARY KEY,
    category      TEXT NOT NULL,
    brand         TEXT NOT NULL,
    price_usd     REAL NOT NULL,
    rating_stars  INTEGER NOT NULL,
    review_count  INTEGER NOT NULL,
    screen_inches REAL,
    ram_gb        INTEGER,
    storage_gb    REAL,
    price_band    TEXT NOT NULL,
    is_outlier    INTEGER NOT NULL
);

-- ---- gold marts ----
DROP TABLE IF EXISTS mart_price_by_category;
CREATE TABLE mart_price_by_category (
    category       TEXT PRIMARY KEY,
    products       INTEGER NOT NULL,
    min_price_usd  REAL NOT NULL,
    max_price_usd  REAL NOT NULL,
    mean_price_usd REAL NOT NULL,
    median_price_usd REAL NOT NULL,
    total_value_usd REAL NOT NULL
);

DROP TABLE IF EXISTS mart_price_by_brand;
CREATE TABLE mart_price_by_brand (
    brand          TEXT PRIMARY KEY,
    products       INTEGER NOT NULL,
    min_price_usd  REAL NOT NULL,
    max_price_usd  REAL NOT NULL,
    mean_price_usd REAL NOT NULL,
    median_price_usd REAL NOT NULL,
    avg_rating     REAL NOT NULL,
    total_reviews  INTEGER NOT NULL
);

DROP TABLE IF EXISTS mart_rating_by_category;
CREATE TABLE mart_rating_by_category (
    category       TEXT PRIMARY KEY,
    products       INTEGER NOT NULL,
    avg_rating     REAL NOT NULL,
    rated_4_plus   INTEGER NOT NULL,
    rated_1        INTEGER NOT NULL,
    zero_reviews   INTEGER NOT NULL,
    total_reviews  INTEGER NOT NULL,
    weighted_rating REAL NOT NULL
);

DROP TABLE IF EXISTS mart_price_bands;
CREATE TABLE mart_price_bands (
    price_band TEXT PRIMARY KEY,
    products   INTEGER NOT NULL,
    share_pct  REAL NOT NULL,
    avg_price_usd REAL NOT NULL
);

DROP TABLE IF EXISTS mart_price_outliers;
CREATE TABLE mart_price_outliers (
    product_id   TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    category     TEXT NOT NULL,
    brand        TEXT NOT NULL,
    price_usd    REAL NOT NULL,
    q1_usd       REAL NOT NULL,
    q3_usd       REAL NOT NULL,
    upper_fence_usd REAL NOT NULL,
    excess_usd   REAL NOT NULL
);

DROP TABLE IF EXISTS mart_top_reviewed;
CREATE TABLE mart_top_reviewed (
    product_id   TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    category     TEXT NOT NULL,
    brand        TEXT NOT NULL,
    price_usd    REAL NOT NULL,
    rating_stars INTEGER NOT NULL,
    review_count INTEGER NOT NULL
);
