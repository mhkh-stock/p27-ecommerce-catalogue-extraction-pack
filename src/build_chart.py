"""Build the 3 charts for P27 from the warehouse marts.

1. avg_price_by_category.png — mean vs median price by category.
2. price_band_distribution.png — products per price band, stacked by category.
3. avg_rating_by_brand.png — average rating by brand (3+ products),
   with product counts.

Usage:  python3 src/build_chart.py
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "catalogue.db"
OUT = ROOT / "outputs"

BLUE = "#2E5A88"
LIGHT = "#7FA8C9"
ORANGE = "#D97A2B"
GREY = "#6B7280"

BANDS = ["Under $300", "$300 - $599", "$600 - $999", "$1000 - $1499", "$1500+"]
BAND_COLOURS = ["#2E5A88", "#5B8DB8", "#8FB3D1", "#D97A2B", "#8B2E2E"]


def chart_price_by_category(conn):
    rows = conn.execute(
        "SELECT category, products, mean_price_usd, median_price_usd "
        "FROM mart_price_by_category ORDER BY products DESC").fetchall()
    cats = [r[0] for r in rows]
    means = [r[2] for r in rows]
    medians = [r[3] for r in rows]
    counts = [r[1] for r in rows]
    x = range(len(cats))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    w = 0.36
    ax.bar([i - w / 2 for i in x], means, w, label="Mean price", color=BLUE)
    ax.bar([i + w / 2 for i in x], medians, w, label="Median price", color=LIGHT)
    for i, (m, md, n) in enumerate(zip(means, medians, counts)):
        ax.text(i - w / 2, m + 30, f"${m:,.0f}", ha="center", fontsize=9)
        ax.text(i + w / 2, md + 30, f"${md:,.0f}", ha="center", fontsize=9)
        ax.text(i, max(m, md) + 130, f"n={n}", ha="center", fontsize=9, color=GREY)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats)
    ax.set_ylabel("Price (USD)")
    ax.set_title("Mean vs median price by category — laptops skew dearer")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, max(max(means), max(medians)) * 1.25)
    fig.tight_layout()
    fig.savefig(OUT / "avg_price_by_category.png", dpi=150)
    plt.close(fig)
    print("avg_price_by_category.png")


def chart_price_bands(conn):
    cats = [r[0] for r in conn.execute(
        "SELECT category FROM mart_price_by_category ORDER BY products DESC")]
    data = {b: [] for b in BANDS}
    for cat in cats:
        counts = dict(conn.execute(
            "SELECT price_band, COUNT(*) FROM silver_catalogue "
            "WHERE category = ? GROUP BY price_band", (cat,)).fetchall())
        for b in BANDS:
            data[b].append(counts.get(b, 0))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    left = [0] * len(cats)
    for b, colour in zip(BANDS, BAND_COLOURS):
        ax.barh(cats, data[b], left=left, label=b, color=colour)
        for i, v in enumerate(data[b]):
            if v:
                ax.text(left[i] + v / 2, i, str(v), ha="center", va="center",
                        fontsize=9, color="white")
        left = [l + v for l, v in zip(left, data[b])]
    ax.set_xlabel("Products")
    ax.set_title("Price-band mix by category — the $600–$999 shelf is nearly empty")
    ax.legend(frameon=False, fontsize=8, loc="upper center",
              bbox_to_anchor=(0.5, -0.12), ncol=5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "price_band_distribution.png", dpi=150)
    plt.close(fig)
    print("price_band_distribution.png")


def chart_rating_by_brand(conn):
    rows = conn.execute(
        "SELECT brand, products, avg_rating FROM mart_price_by_brand "
        "WHERE products >= 3 ORDER BY avg_rating ASC").fetchall()
    brands = [f"{r[0]} (n={r[1]})" for r in rows]
    ratings = [r[2] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    colours = [ORANGE if r < 2.0 else BLUE for r in ratings]
    ax.barh(brands, ratings, color=colours)
    for i, r in enumerate(ratings):
        ax.text(r + 0.05, i, f"{r:.2f}", va="center", fontsize=9)
    ax.set_xlim(0, 3.5)
    ax.set_xlabel("Average rating (stars, 1–5)")
    ax.set_title("Average rating by brand (3+ products) — no brand averages above 3")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "avg_rating_by_brand.png", dpi=150)
    plt.close(fig)
    print("avg_rating_by_brand.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    chart_price_by_category(conn)
    chart_price_bands(conn)
    chart_rating_by_brand(conn)
    conn.close()


if __name__ == "__main__":
    main()
