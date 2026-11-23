# P27 — E-commerce Catalogue Extraction Pack

**Client (SAMPLE):** a retailer who wants their competitor's catalogue
in a spreadsheet · **Status: SAMPLE delivery on a LIVE scrape**
**Tools:** Python (requests + BeautifulSoup) · SQL (SQLite) · Excel
(live formulas) · reportlab
**Deliverable:** `outputs/catalogue_SAMPLE.xlsx` +
`outputs/catalogue_report_SAMPLE.pdf` — the competitor's full listed
catalogue plus the price and rating analysis

> ⚠️ **What this is and is not.** The catalogue is real data scraped
> live on 23 Nov 2026 from webscraper.io, a public e-commerce
> practice site built for scraping practice — Laptops, Tablets and
> Touch (phones), 147 products. It stands in for a competitor's
> catalogue: the client, the rivalry and the recommendations are the
> sample framing, not a real business. What is real is the method —
> the same scrape → warehouse → checks → workbook + report pipeline
> runs unchanged on a real competitor's site, and every number in the
> report is recomputed from the scraped data, never typed.

## Business question it answers

> "My competitor's catalogue, in a spreadsheet."

A retailer who cannot see the rival's range is guessing: which price
bands the rival actually covers, where the gaps are, which of their
products buyers trust and which they pan. This delivery answers it
with a warehouse (147 products in a star schema), 14 data-quality
tests that all pass, and a workbook whose headline numbers are live
formulas — so the client can filter the catalogue, see the price
gap and the rating problem, and act on both.

## The method (plainly stated)

**Scrape:** one polite request per category page (1s apart, browser
User-Agent), parsing the listing cards — title, listed price, whole-star
rating, review count, description, product URL. Each category page
lists every product; the site's `?page=2` returns the same list, so
there is no pagination to walk. The scrape log records every URL,
status and count.

**Clean:** price parsed from `$295.99` text to USD; brand normalised
from the title (the first word is a sub-brand or model line on this
site — ThinkPad, Aspire, Galaxy, Hewlett, Pavilion, ProBook,
Inspiron, IdeaTab, iPad, iPhone, Iconia, MeMO — mapped to the maker);
screen size, RAM and storage parsed from the description where stated;
price bands fixed at Under $300 / $300–$599 / $600–$999 / $1000–$1499
/ $1500+.

**Outliers:** per-category IQR fence (Q3 + 1.5 × IQR). No product in
this catalogue is priced above its category fence — **0 outliers**,
which is itself a finding: the range has no extreme prices to explain
away.

**Ratings:** whole stars 1–5 as listed. The catalogue holds **no
5-star product** — the highest listed rating is 4 stars. The average
is 2.37 stars; the review-weighted average is 2.47.

**Limits, stated upfront:** the site publishes no stock status, no
seller name and no sales volume, so this pack claims none of those.
Prices are a single-day snapshot (23 Nov 2026) — re-run
`src/scrape.py` for a fresh one. Specs are partial (screen 134/147,
RAM 135/147, storage 87/147): blank means the listing does not state
the spec, not zero. The Touch category is only 9 phones, so its
averages rest on a small base.

## What is inside

| File | What it does |
|---|---|
| `outputs/catalogue_SAMPLE.xlsx` | The deliverable: Cover (headline numbers, live) + Catalogue (147 products, filterable) + Summary (21 headline numbers, all formulas) + Price by category + Price by brand + Ratings + Method |
| `outputs/catalogue_report_SAMPLE.pdf` | 2-page report: question, headline numbers, tables, method, recommendations |
| `outputs/avg_price_by_category.png` | Chart: mean vs median price by category |
| `outputs/price_band_distribution.png` | Chart: price-band mix by category |
| `outputs/avg_rating_by_brand.png` | Chart: average rating by brand (3+ products) |
| `outputs/dq_report.md` | Findings report: 14/14 test results, reconciliation |
| `outputs/test_results.json` | Machine-readable test results (14 tests) |
| `outputs/analysis.json` | Headline numbers, computed once from the warehouse |
| `outputs/mart_*.csv` | The six gold marts as CSVs (price by category/brand, rating by category, price bands, outliers, top reviewed) |
| `data/raw/catalogue_SAMPLE.csv` | The scraped listing: 147 rows, exactly as listed |
| `data/raw/scrape_log.json` | What was fetched, when, how many |
| `data/processed/catalogue.db` | The built warehouse (SQLite — NOT committed; rebuilds from the scripts) |
| `data/processed/fact_catalogue.csv` | The fact table as CSV (147 rows) |
| `data/README.md` | Data dictionary + brand map + known quirks |
| `sql/schema.sql` | Bronze landing table + gold star-schema DDL |
| `sql/silver_catalogue.sql` | Silver model (price parse, brand normalisation, price bands) |
| `sql/gold_dimensions.sql`, `gold_facts.sql`, `gold_marts.sql` | Gold models (dimensions + fact + 6 marts) |
| `sql/tests/` | 14 data-quality test queries (bronze counts, silver guards, gold grain, reconciliation) |
| `src/scrape.py` | The live scraper (3 category pages, polite, logged) |
| `src/build_pipeline.py` | Runs bronze → silver → gold into `catalogue.db`, prints row counts |
| `src/headlines.py` | Headline numbers from the warehouse, written to `outputs/analysis.json` |
| `src/run_tests.py` | Runs all 14 tests, prints PASS/FAIL per test + summary |
| `src/build_chart.py` | Builds the 3 charts from the warehouse |
| `src/build_workbook.py` | Builds the workbook: 7 sheets, live formulas |
| `src/build_report.py` | Builds the 2-page report PDF + `dq_report.md` |
| `src/checks.py` | Verification suite — 152 checks, all passing (incl. LibreOffice recalc) |
| `requirements.txt` | Pinned: `requests==2.31.0`, `beautifulsoup4==4.15.0`, `openpyxl==3.1.2`, `reportlab==5.0.1`, `matplotlib==3.6.3` (Python 3.12) |

## How it fits together

```
webscraper.io practice site (Laptops 117 / Tablets 21 / Touch 9)
   ──▶ src/scrape.py ──▶ data/raw/catalogue_SAMPLE.csv (147 rows)
                                                        ▼
                                           bronze_catalogue ──▶ silver_catalogue
                                           (price parse, brand map, bands,
                                            specs from descriptions)
                                                        ▼
                              dim_category + dim_brand ──▶ fact_catalogue
                                                        ▼
              mart_price_by_category / _brand / mart_rating_by_category
              mart_price_bands / mart_price_outliers (0) / mart_top_reviewed
                                                        ▼
                     src/build_workbook.py ──▶ catalogue_SAMPLE.xlsx
                     src/build_report.py   ──▶ catalogue_report_SAMPLE.pdf
                     src/build_chart.py    ──▶ 3 charts
                        ▲ src/checks.py verifies all of it (152 checks)
```

## Headline numbers (SAMPLE — live scrape, 23 Nov 2026)

- **147 products · 3 categories · 16 brands** · **catalogue value
  $114,877.78**
- **Price range $24.99 – $1,799.00** · **mean $781.48 · median $739.99**
- **Average rating 2.37 stars (of 5)** · **review-weighted 2.47** ·
  **1,033 reviews**
- **27 products rated 4+ stars (18.37%)** · **43 rated 1 star (29.25%)**
  · **no 5-star product in the whole catalogue**
- **8 products with no reviews** (all laptops)
- **0 price outliers** (per-category IQR fence)
- **14/14 data-quality tests passing** · **152 automated checks passing**

## Price by category (USD)

| Category | Products | Min | Max | Mean | Median | Total value |
|---|---|---|---|---|---|---|
| Laptops | 117 | $295.99 | $1,799.00 | $909.39 | $1,102.66 | $106,399.08 |
| Tablets | 21 | $69.99 | $603.99 | $232.04 | $130.99 | $4,872.79 |
| Touch | 9 | $24.99 | $899.99 | $400.66 | $118.99 | $3,605.91 |
| **TOTAL** | **147** | **$24.99** | **$1,799.00** | **$781.48** | **$739.99** | **$114,877.78** |

Laptops carry the catalogue: 117 of 147 products and $106,399.08 of
the $114,877.78 total value. Their median ($1,102.66) sits above their
mean ($909.39) — the range is two shelves, not one: budget machines
near $300 and premium machines above $1,100, with little in between.
Tablets are the budget shelf (median $130.99). Touch is nine phones,
three of them iPhones at $899.99.

## Price bands — the gap in the middle

| Price band | Products | Share | Avg price |
|---|---|---|---|
| Under $300 | 23 | 15.65% | $140.51 |
| $300 - $599 | 45 | 30.61% | $445.60 |
| $600 - $999 | 14 | 9.52% | $785.21 |
| $1000 - $1499 | 62 | 42.18% | $1,213.94 |
| $1500+ | 3 | 2.04% | $1,779.00 |
| **TOTAL** | **147** | **100.00%** | **$781.48** |

42.18% of the catalogue sits at $1,000–$1,499 while only 9.52% sits
at $600–$999. A competitor priced into that empty $600–$999 band
faces almost no listed competition. Only 3 products break $1,500 —
the most expensive is the Asus ROG Strix SCAR Edition at $1,799.00.

## Ratings by category (stars, 1–5)

| Category | Products | Avg rating | Rated 4+ | Rated 1 | No reviews | Total reviews | Weighted |
|---|---|---|---|---|---|---|---|
| Laptops | 117 | 2.34 | 21 | 37 | 8 | 807 | 2.46 |
| Tablets | 21 | 2.67 | 5 | 2 | 0 | 170 | 2.60 |
| Touch | 9 | 2.11 | 1 | 4 | 0 | 56 | 2.25 |
| **TOTAL** | **147** | **2.37** | **27** | **43** | **8** | **1,033** | **2.47** |

The average rating is 2.37 stars and no product is rated 5 stars.
43 products (29.25%) sit at 1 star — nearly a third of the range.
Only 27 (18.37%) reach 4 stars. And the dearer products are not the
better-rated ones: 1-star products average $901.85 while 4-star
products average $673.80. Tablets rate best (2.67), Touch worst
(2.11).

## Price by brand (top 9 by products)

| Brand | Products | Min | Max | Mean | Median | Avg rating | Reviews |
|---|---|---|---|---|---|---|---|
| Lenovo | 30 | $69.99 | $1,399.00 | $788.10 | $1,016.50 | 2.53 | 240 |
| Acer | 29 | $96.99 | $1,221.58 | $586.45 | $457.38 | 2.45 | 161 |
| Asus | 23 | $101.99 | $1,799.00 | $851.46 | $799.00 | 2.30 | 164 |
| Dell | 21 | $488.78 | $1,341.22 | $1,090.33 | $1,144.20 | 2.43 | 158 |
| Apple | 8 | $537.99 | $1,347.78 | $972.86 | $899.99 | 2.00 | 53 |
| Samsung | 8 | $93.99 | $587.99 | $282.99 | $242.99 | 2.88 | 61 |
| HP | 7 | $364.46 | $1,326.83 | $773.34 | $609.99 | 2.00 | 57 |
| MSI | 7 | $1,099.00 | $1,299.00 | $1,174.71 | $1,179.00 | 1.86 | 43 |
| Toshiba | 5 | $1,114.55 | $1,366.32 | $1,226.61 | $1,203.41 | 1.60 | 37 |

Samsung rates best of the big brands (2.88) and Toshiba worst (1.60).
Dell is the dearest big brand on average ($1,090.33); MSI and Toshiba
sell nothing under $1,099. The remaining 7 brands (Amazon, LG, Nokia,
Packard Bell, Prestigio, Sony, Ubuntu) hold 8 products between them.

## Most-reviewed products (14 reviews each — the proven sellers)

| Product | Category | Price | Rating | Reviews |
|---|---|---|---|---|
| Asus MeMO Pad | Tablets | $102.99 | 4 | 14 |
| Acer Aspire ES1-732 Black | Laptops | $410.46 | 4 | 14 |
| Dell Vostro 15 | Laptops | $488.78 | 4 | 14 |
| Lenovo ThinkPad L460 | Laptops | $1,096.02 | 4 | 14 |
| Dell Latitude 5480 | Laptops | $1,133.82 | 4 | 14 |

Five products share the maximum 14 reviews, and all five are rated
4 stars — the competitor's trusted core. The worst-rated product with
10+ reviews is the Asus ZenBook UX530UX-FY040T Blue at 1 star on 14
reviews: a premium-priced laptop ($1,239.20) buyers actively dislike.

## The three recommendations (from the data, not from a template)

1. **Price into the $600–$999 gap.** Only 14 of 147 products sit
   there while 62 sit at $1,000–$1,499. A mid-range laptop or tablet
   in that band meets buyers the competitor barely serves.
2. **Attack on ratings, not on price.** The competitor's range
   averages 2.37 stars with no 5-star product and 29.25% at 1 star —
   and its dearest products rate worst. A 4-star product at $400–$600
   beats their $1,100 1-star machines on the comparison a buyer
   actually makes.
3. **Watch the five proven sellers.** The 4-star products with 14
   reviews are the competitor's trusted core. Any matching product
   should be compared against them on price first, and their 1-star
   premium laptops (ZenBook UX530UX, Legion Y520) are the weakest
   premium listings to displace.

## Same logic, four ways — and they must agree

The headline numbers exist in four forms: the raw scraped CSV, the
SQL warehouse, the workbook's formulas, and the report PDF.
`src/checks.py` recomputes all four from the raw file and compares
them — a mistake in any one shows up as a failure. The workbook's
formulas were also recalculated in LibreOffice: every total matches
the recompute exactly, with zero error values.

## Reproduce it (2 minutes)

```bash
pip install -r requirements.txt
python3 src/scrape.py          # live scrape -> data/raw/catalogue_SAMPLE.csv
python3 src/build_pipeline.py  # bronze -> silver -> gold -> data/processed/catalogue.db
python3 src/run_tests.py       # 14 tests — expect 14/14 passing
python3 src/headlines.py       # headline numbers -> outputs/analysis.json
python3 src/build_chart.py     # 3 charts
python3 src/build_workbook.py  # outputs/catalogue_SAMPLE.xlsx
python3 src/build_report.py    # outputs/catalogue_report_SAMPLE.pdf (2 pages) + dq_report.md
python3 src/checks.py          # 152 checks — expect all passing
```

On a real competitor's site, point `src/scrape.py` at that site's
category pages (same card fields: title, price, rating, review count,
description) and everything downstream runs unchanged. The `.db`
file is never committed; it rebuilds from the scripts.
