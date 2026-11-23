"""P27 — scrape the webscraper.io e-commerce test site (practice site).

The site exists to practise scraping, so fetching its catalogue pages is
its intended use. Three leaf categories under /allinone are scraped:
Laptops, Tablets and Touch (phones). Each category page lists every
product on one page (no working pagination — ?page=2 returns the same
list), so one request per category is enough. Polite: 1s between
requests, a browser User-Agent, no retries hammering the server.

Writes data/raw/catalogue_SAMPLE.csv (one row per product, exactly as
listed) and data/raw/scrape_log.json (what was fetched, when, how many).

Usage:  python3 src/scrape.py
"""
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
BASE = "https://webscraper.io"
CATEGORIES = [
    ("Laptops", "/test-sites/e-commerce/allinone/computers/laptops"),
    ("Tablets", "/test-sites/e-commerce/allinone/computers/tablets"),
    ("Touch", "/test-sites/e-commerce/allinone/phones/touch"),
]
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
FIELDS = ["product_id", "category", "title", "price_usd_raw", "rating_stars",
          "review_count", "description", "product_url", "scraped_at"]


def scrape_category(session, category, path):
    url = BASE + path
    resp = session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = []
    for card in soup.select(".thumbnail"):
        link = card.select_one("a.title")
        if not link:
            continue
        href = link.get("href", "")
        product_id = href.rstrip("/").split("/")[-1]
        title = (link.get("title") or link.get_text(strip=True)).strip()
        price_el = card.select_one("span[itemprop='price']")
        price_raw = price_el.get_text(strip=True) if price_el else ""
        rating_el = card.select_one("p[data-rating]")
        rating = rating_el.get("data-rating") if rating_el else ""
        reviews_el = card.select_one("span[itemprop='reviewCount']")
        reviews = reviews_el.get_text(strip=True) if reviews_el else ""
        desc_el = card.select_one("p.description")
        desc = desc_el.get_text(" ", strip=True) if desc_el else ""
        rows.append({
            "product_id": product_id,
            "category": category,
            "title": title,
            "price_usd_raw": price_raw,
            "rating_stars": rating,
            "review_count": reviews,
            "description": desc,
            "product_url": BASE + href,
            "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    return resp.status_code, rows


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    all_rows = []
    log = {"source": "https://webscraper.io/test-sites/e-commerce/allinone",
           "scraped_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "categories": []}
    for i, (category, path) in enumerate(CATEGORIES):
        if i:
            time.sleep(1)  # polite pause between requests
        status, rows = scrape_category(session, category, path)
        log["categories"].append({"category": category, "url": BASE + path,
                                  "http_status": status, "products": len(rows)})
        print(f"{category}: {len(rows)} products (HTTP {status})")
        all_rows.extend(rows)

    # dedupe on product_id (same product must not appear twice)
    seen, unique = set(), []
    for r in all_rows:
        if r["product_id"] in seen:
            print(f"WARNING duplicate product_id dropped: {r['product_id']}")
            continue
        seen.add(r["product_id"])
        unique.append(r)
    log["total_products"] = len(unique)
    log["duplicates_dropped"] = len(all_rows) - len(unique)

    out = RAW / "catalogue_SAMPLE.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(unique)
    (RAW / "scrape_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"{len(unique)} products -> {out}")
    print(f"log -> {RAW / 'scrape_log.json'}")


if __name__ == "__main__":
    main()
