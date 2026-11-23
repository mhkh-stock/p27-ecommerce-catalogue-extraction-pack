# P27 — Package Note (Fiverr-ready)

**Gig title:** I will scrape your competitor's catalogue into a spreadsheet with price and rating analysis

**What the client gets:** their competitor's full listed catalogue
in a spreadsheet — every product with its price, rating, review
count, brand and specs — plus the analysis that makes it usable:
price by category and brand with mean vs median, the price-band mix
with the gaps named, rating analysis by category and brand
(including the review-weighted average), the most-reviewed products
ranked, the cheapest and dearest products, a per-category IQR
outlier check, 14 data-quality tests that catch duplicates, prices
that do not parse, ratings out of range and rows that do not add up,
a reconciliation report proving the money agrees from the raw scrape
to the warehouse to the workbook, a live Excel workbook (every
headline number a formula), three charts, and a 2-page report they
can hand to the owner. Delivered as a GitHub repo they can re-run
on a fresh scrape themselves.

**Honest note (in the repo, stated plainly):** this is a sample
delivery on a live scrape of a public e-commerce practice site —
the skill and the method are real, the competitor is not. The site
publishes no stock status, seller name or sales volume, so this
service never claims those; on a real competitor's site the same
fields are extracted only where the site actually lists them. Prices
are a single-day snapshot and the workbook re-runs on a fresh scrape.

## Tiers (Hashir's band)

| Tier | Price | Delivery | Includes |
|---|---|---|---|
| Basic | $20 | 2 days | The scrape of one competitor site (up to 3 categories, up to 150 products): the cleaned catalogue CSV + the Excel workbook with the full product list, the 14 data-quality tests with a pass/fail report |
| Standard | $65 | 4 days | Everything in Basic + price analysis by category and brand (mean vs median), the price-band mix with the gaps named, rating analysis by category and brand, the most-reviewed products ranked, the 3 charts, the 2-page report PDF, the reconciliation proof (raw scrape → warehouse → workbook to the cent) |
| Premium | $140 | 6 days | Everything in Standard + up to 3 competitor sites (or 6 categories on one site), the cheapest/dearest products and the IQR outlier check, brand normalisation across sub-brands and model lines, a second scrape run a week later to show price moves, a 1-page owner guide (how to re-run the scrape and refresh the workbook), 1 revision round |

**What's NOT included:** scraping a site that forbids it in its
terms or behind a login/paywall (this service scrapes public
listings only — quoted separately if the site needs an approved
data feed); stock levels or sales volumes the site does not publish
(this service reports only what the listing shows); changing their
prices (this service shows them what the competitor lists — the
positioning advice uses the competitor's own numbers); a live
dashboard that updates itself (this service is a warehouse + a
workbook they re-run — a live dashboard is a different gig);
monitoring the competitor daily (quoted separately as a recurring
scrape).

**Delivery time note:** counts from the day the client names the
competitor site and its category pages, not from order placement.

**Proof this service works:** this repo's SAMPLE — a live scrape of
the webscraper.io e-commerce practice site on 23 Nov 2026, 147
products across 3 categories (Laptops 117, Tablets 21, Touch 9) and
16 brands, catalogue value $114,877.78, price range $24.99–$1,799.00
(mean $781.48, median $739.99), average rating 2.37 stars with no
5-star product in the whole catalogue, 1,033 reviews, 27 products
rated 4+ stars (18.37%) against 43 rated 1 star (29.25%), 8 products
with no reviews, 0 price outliers by the per-category IQR fence,
the $600–$999 band nearly empty (14 of 147 products) against 62 at
$1,000–$1,499, laptops carrying $106,399.08 of the value with a
median ($1,102.66) above their mean ($909.39), 1-star products
averaging $901.85 against $673.80 for 4-star products, five proven
sellers sharing the maximum 14 reviews (all rated 4 stars), 14/14
data-quality tests passing, 152 automated checks passing including
a LibreOffice recalculation of the workbook with zero error values
and a verified 2-page report PDF, and 3 recommendations the owner
can act on — price into the $600–$999 gap, attack on ratings not
price, watch the five proven sellers.
