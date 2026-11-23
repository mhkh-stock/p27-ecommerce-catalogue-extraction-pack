"""P27 — headline numbers, computed once from the warehouse.

Single source of truth for the report PDF, the workbook and the
README figures: every consumer imports compute_headlines() instead
of re-typing numbers. src/checks.py deliberately does NOT use this
module — it recomputes the same numbers from the raw CSV so a bug
here shows up as a mismatch.
"""
import json
import sqlite3
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "catalogue.db"


def compute_headlines(conn):
    h = {}
    h["products"] = conn.execute("SELECT COUNT(*) FROM fact_catalogue").fetchone()[0]
    h["categories"] = conn.execute("SELECT COUNT(*) FROM dim_category").fetchone()[0]
    h["brands"] = conn.execute("SELECT COUNT(*) FROM dim_brand").fetchone()[0]
    prices = [r[0] for r in conn.execute("SELECT price_usd FROM fact_catalogue")]
    h["total_value_usd"] = round(sum(prices), 2)
    h["price_min"] = min(prices)
    h["price_max"] = max(prices)
    h["price_mean"] = round(statistics.mean(prices), 2)
    h["price_median"] = round(statistics.median(prices), 2)
    h["avg_rating"] = round(
        conn.execute("SELECT AVG(rating_stars) FROM fact_catalogue").fetchone()[0], 2)
    h["weighted_rating"] = round(
        conn.execute("SELECT SUM(rating_stars * review_count) * 1.0 "
                     "/ SUM(review_count) FROM fact_catalogue").fetchone()[0], 2)
    h["rated_4_plus"] = conn.execute(
        "SELECT COUNT(*) FROM fact_catalogue WHERE rating_stars >= 4").fetchone()[0]
    h["rated_1"] = conn.execute(
        "SELECT COUNT(*) FROM fact_catalogue WHERE rating_stars = 1").fetchone()[0]
    h["rated_5"] = conn.execute(
        "SELECT COUNT(*) FROM fact_catalogue WHERE rating_stars = 5").fetchone()[0]
    h["zero_reviews"] = conn.execute(
        "SELECT COUNT(*) FROM fact_catalogue WHERE review_count = 0").fetchone()[0]
    h["total_reviews"] = conn.execute(
        "SELECT SUM(review_count) FROM fact_catalogue").fetchone()[0]
    h["outliers"] = conn.execute(
        "SELECT COUNT(*) FROM mart_price_outliers").fetchone()[0]
    h["price_by_category"] = [
        dict(zip(["category", "products", "min", "max", "mean", "median", "total"],
                 r))
        for r in conn.execute("SELECT * FROM mart_price_by_category ORDER BY products DESC")]
    h["price_by_brand"] = [
        dict(zip(["brand", "products", "min", "max", "mean", "median",
                  "avg_rating", "total_reviews"], r))
        for r in conn.execute("SELECT * FROM mart_price_by_brand ORDER BY products DESC")]
    h["rating_by_category"] = [
        dict(zip(["category", "products", "avg_rating", "rated_4_plus", "rated_1",
                  "zero_reviews", "total_reviews", "weighted_rating"], r))
        for r in conn.execute("SELECT * FROM mart_rating_by_category ORDER BY products DESC")]
    h["price_bands"] = [
        dict(zip(["band", "products", "share_pct", "avg_price"], r))
        for r in conn.execute(
            "SELECT * FROM mart_price_bands ORDER BY "
            "CASE price_band WHEN 'Under $300' THEN 1 WHEN '$300 - $599' THEN 2 "
            "WHEN '$600 - $999' THEN 3 WHEN '$1000 - $1499' THEN 4 ELSE 5 END")]
    h["rating_dist"] = [
        {"stars": r[0], "products": r[1]}
        for r in conn.execute("SELECT rating_stars, COUNT(*) FROM fact_catalogue "
                              "GROUP BY rating_stars ORDER BY rating_stars")]
    h["top_reviewed"] = [
        dict(zip(["product_id", "title", "category", "brand", "price",
                  "rating", "reviews"], r))
        for r in conn.execute("SELECT * FROM mart_top_reviewed")]
    h["most_expensive"] = [
        dict(zip(["title", "category", "brand", "price", "rating", "reviews"], r))
        for r in conn.execute(
            "SELECT s.title, f.category, f.brand, f.price_usd, f.rating_stars, "
            "f.review_count FROM fact_catalogue f JOIN silver_catalogue s "
            "USING (product_id) ORDER BY f.price_usd DESC LIMIT 5")]
    h["cheapest"] = [
        dict(zip(["title", "category", "brand", "price", "rating", "reviews"], r))
        for r in conn.execute(
            "SELECT s.title, f.category, f.brand, f.price_usd, f.rating_stars, "
            "f.review_count FROM fact_catalogue f JOIN silver_catalogue s "
            "USING (product_id) ORDER BY f.price_usd ASC LIMIT 5")]
    h["avg_price_by_rating"] = [
        {"stars": r[0], "avg_price": round(r[1], 2), "products": r[2]}
        for r in conn.execute("SELECT rating_stars, AVG(price_usd), COUNT(*) "
                              "FROM fact_catalogue GROUP BY rating_stars ORDER BY rating_stars")]
    h["spec_coverage"] = {
        "screen": conn.execute(
            "SELECT COUNT(*) FROM silver_catalogue WHERE screen_inches IS NOT NULL").fetchone()[0],
        "ram": conn.execute(
            "SELECT COUNT(*) FROM silver_catalogue WHERE ram_gb IS NOT NULL").fetchone()[0],
        "storage": conn.execute(
            "SELECT COUNT(*) FROM silver_catalogue WHERE storage_gb IS NOT NULL").fetchone()[0],
    }
    return h


def main():
    conn = sqlite3.connect(DB)
    h = compute_headlines(conn)
    conn.close()
    out = ROOT / "outputs" / "analysis.json"
    out.write_text(json.dumps(h, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    for k in ["products", "categories", "brands", "price_min", "price_max",
              "price_mean", "price_median", "avg_rating", "total_reviews",
              "rated_4_plus", "rated_1", "zero_reviews", "outliers"]:
        print(f"  {k}: {h[k]}")


if __name__ == "__main__":
    main()
