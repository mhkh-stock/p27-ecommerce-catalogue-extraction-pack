# Data — P27 E-commerce Catalogue Extraction Pack

## Source

Scraped **live** from the webscraper.io e-commerce practice site
(a site built for scraping practice) on 23 Nov 2026 — no synthetic
fallback was needed. `src/scrape.py` fetches one page per category;
each page lists every product (the site's `?page=2` returns the same
list, so there is no pagination to walk). 3 categories, 147 products,
all HTTP 200. See `scrape_log.json` for the exact URLs, timestamps
and per-category counts.

| File | Rows | What it is |
|---|---|---|
| `raw/catalogue_SAMPLE.csv` | 147 | The scraped listing, exactly as listed: product id, category, title, price as listed (`$295.99`), whole-star rating, review count, description, product URL, scrape timestamp |
| `raw/scrape_log.json` | — | What was fetched, when, how many per category |
| `processed/fact_catalogue.csv` | 147 | The gold fact table (one row per product) |
| `processed/catalogue.db` | — | The built warehouse (SQLite — **NOT committed**; rebuilds from the scripts) |

The `_SAMPLE` suffix marks this as demo data from a public practice
catalogue, not a real competitor — the method is the deliverable.

## Data dictionary — `raw/catalogue_SAMPLE.csv`

| Column | Type | Meaning |
|---|---|---|
| `product_id` | text | The site's product id (from the product URL), unique |
| `category` | text | Laptops / Tablets / Touch (phones) |
| `title` | text | Product title as listed |
| `price_usd_raw` | text | Listed price, e.g. `$295.99` — parsed to `price_usd` in silver |
| `rating_stars` | integer | Whole stars 1–5 as listed (this catalogue: 1–4 only, no 5-star product) |
| `review_count` | integer | Reviews shown on the listing (0–14) |
| `description` | text | Listing description — screen size, RAM and storage are parsed from this in the pipeline |
| `product_url` | text | Canonical product page on webscraper.io |
| `scraped_at` | timestamp | UTC scrape time |

## Data dictionary — `processed/fact_catalogue.csv`

| Column | Type | Meaning |
|---|---|---|
| `product_id` | text | Unique product id |
| `category` | text | Laptops / Tablets / Touch |
| `brand` | text | Maker, normalised from the title (see below) |
| `price_usd` | real | Parsed price in USD |
| `rating_stars` | integer | 1–4 in this catalogue |
| `review_count` | integer | 0–14 |
| `screen_inches` | real | Parsed from description, or blank where the listing does not state it (134/147) |
| `ram_gb` | integer | Parsed from description, or blank (135/147) |
| `storage_gb` | real | Parsed from description, or blank (87/147) |
| `price_band` | text | Under $300 / $300–$599 / $600–$999 / $1000–$1499 / $1500+ |
| `is_outlier` | integer | 1 if priced above its category IQR fence — 0 for every product here |

## Brand normalisation

The first word of a title is not the brand on this site — sub-brands
and model lines sit there instead. Silver maps them to the maker:
ThinkPad/Lenovo/IdeaTab → Lenovo; Aspire/Acer/Iconia → Acer;
Hewlett/HP/Pavilion/ProBook → HP; Dell/Inspiron → Dell; Apple/iPhone/
iPad → Apple; Samsung/Galaxy → Samsung; Asus/MeMO → Asus;
Packard → Packard Bell. Anything unmapped keeps its first word.
Result: 16 brands. Test `t09` proves no raw sub-brand survives.

## Known quirks (stated, not hidden)

- **No 5-star product exists** in this catalogue — the highest listed
  rating is 4 stars. The 2.37 average is the site's own data, not a
  cleaning choice.
- **Ratings are whole stars only** — the site lists no half stars.
- **No stock status is published** by the site, so none is in this
  pack. Do not read stock into it.
- **Laptops are bimodal**: median $1,102.66 sits above the mean
  $909.39 — budget machines near $300 and premium machines above
  $1,100, with little in between. The $600–$999 band holds only 14
  of 147 products.
- **Touch is 9 phones**, three of them iPhones all listed at $899.99.
- **Specs are partial**: storage is stated on only 87 of 147 listings.
  Blank means "not stated", not zero.
- **Prices are a single-day snapshot** (23 Nov 2026). Re-run
  `src/scrape.py` for a fresh snapshot; the pipeline is idempotent.
