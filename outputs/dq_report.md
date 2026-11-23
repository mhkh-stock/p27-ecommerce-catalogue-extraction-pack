# P27 — Data-quality report

**14/14 tests passing.** Each test is a SQL query in `sql/tests/` that returns its violating rows; every test expects 0 rows.

| Test | Result | Violations |
|---|---|---|
| `t01_bronze_row_count.sql` | PASS | 0 |
| `t02_bronze_duplicate_product_id.sql` | PASS | 0 |
| `t03_bronze_price_parses.sql` | PASS | 0 |
| `t04_bronze_rating_range.sql` | PASS | 0 |
| `t05_bronze_review_count_valid.sql` | PASS | 0 |
| `t06_bronze_product_url.sql` | PASS | 0 |
| `t07_silver_no_nulls.sql` | PASS | 0 |
| `t08_silver_price_band_assigned.sql` | PASS | 0 |
| `t09_silver_brand_normalised.sql` | PASS | 0 |
| `t10_fact_grain.sql` | PASS | 0 |
| `t11_fact_totals_reconcile.sql` | PASS | 0 |
| `t12_mart_price_by_category_reconciles.sql` | PASS | 0 |
| `t13_mart_rating_by_category_reconciles.sql` | PASS | 0 |
| `t14_outliers_complete_and_valid.sql` | PASS | 0 |

## What the tests cover

- **Bronze (t01–t06):** row count matches the raw CSV (147), no duplicate product, every price parses to a positive number, ratings are whole stars 1–5, review counts are non-negative, every product URL points at the site.
- **Silver (t07–t09):** no NULL price/brand/category/title, every row carries one of the five price bands, no raw sub-brand (ThinkPad, Aspire, Galaxy, …) survives the brand normalisation.
- **Gold (t10–t14):** fact grain is one row per product, fact totals reconcile to silver, both marts reconcile, and the outlier mart is complete and valid (0 outliers — no product is priced above its category IQR fence).

## Reconciliation

- Raw CSV rows: 147 → bronze: 147 → silver: 147 → fact: 147. Nothing dropped, nothing added.
- Catalogue value: $114,877.78 in bronze (parsed), silver, fact and the marts — the same number four ways.
- Reviews: 1,033 in silver, fact and the rating mart.
- Spec coverage from descriptions: screen 134/147, RAM 135/147, storage 87/147. Blank means the listing does not state the spec, not zero.

## Checks beyond the SQL tests

src/checks.py recomputes every headline number from the raw CSV independently (no database, no warehouse) and compares it with the warehouse, the workbook's formulas (recalculated in LibreOffice) and this report. See its output for the full list.
