"""
One-click Shopify migration.

Set `export_format="shopify-csv"` and the actor returns
ready-to-import Shopify Product CSV rows for every successful product
(Handle, Title, Body HTML, Vendor, Type, Tags, Variant Price, Image
Src, SEO Title/Description, Status — 19 columns).

Save the result as a `.csv` and upload at
**Shopify Admin → Products → Import**.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/shopify_csv_migration.py
"""

from __future__ import annotations

import csv

from temu_scraper import TemuScraperClient

URLS = [
    "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    # ...add the Temu URLs you want to clone into your Shopify store
]


def main() -> None:
    client = TemuScraperClient()

    # Server-side: drop weak picks before they hit your CSV
    products, _ = client.scrape(
        URLS,
        retail_markup=3.5,                # 3.5× = healthy margin for Shopify
        min_hot_product_score=55,
        only_free_shipping=True,
        export_format="shopify-csv",      # ← key switch
        write_summary=False,
    )
    if not products:
        print("No products survived the filters.")
        return

    # Each row is already a flat dict matching Shopify columns —
    # write straight to a CSV file.
    fieldnames = list(products[0].keys())
    with open("shopify_import.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in products:
            writer.writerow(row)

    print(f"Wrote {len(products)} rows to shopify_import.csv")
    print("Upload at Shopify Admin → Products → Import.")


if __name__ == "__main__":
    main()
