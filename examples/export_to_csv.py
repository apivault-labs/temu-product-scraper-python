"""
Flat CSV export — useful for ad-hoc spreadsheet analysis or dropping
into BigQuery / a BI tool. Picks the most actionable fields rather
than dumping everything.

For a Shopify-import-ready CSV, see ``shopify_csv_migration.py``.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/export_to_csv.py
"""

from __future__ import annotations

import csv

from temu_scraper import TemuScraperClient


URLS = [
    "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    # ...
]

COLUMNS = [
    "productId", "title", "shopName", "autoCategory",
    "priceUsd", "originalPriceUsd", "discountPct", "savingsUsd",
    "currency", "freeShipping",
    "rating", "reviewsCountInt", "soldCountInt", "soldCountTier",
    "isTrending",
    "demandScore", "demandTier",
    "estimatedRetailUsd", "estimatedProfitMarginPct", "arbitrage_tier",
    "hotProductScore", "hotProductTier",
    "imagesCount", "variantsCount",
    "riskCount",
    "productUrl",
]


def main() -> None:
    client = TemuScraperClient()

    products, _ = client.scrape(
        URLS,
        retail_markup=3.0,
        min_demand_score=20,
        write_summary=False,
    )
    print(f"Got {len(products)} products")

    # Keep the actionable fields only
    rows = []
    for p in products:
        rows.append({col: p.get(col, "") for col in COLUMNS})

    with open("temu_products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to temu_products.csv "
          f"({len(COLUMNS)} columns)")


if __name__ == "__main__":
    main()
