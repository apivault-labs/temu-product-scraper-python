"""
Google Shopping ads feed export.

Set `export_format="google-merchant"` to receive Google Merchant
Center feed rows (id, title, description, link, image_link,
availability, price, brand, condition, google_product_category) for
every scraped product. Drop the resulting JSON straight into Google
Merchant Center as a scheduled feed.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/google_merchant_feed.py
"""

from __future__ import annotations

import json

from temu_scraper import TemuScraperClient


URLS = [
    "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    # ...
]


def main() -> None:
    client = TemuScraperClient()

    products, _ = client.scrape(
        URLS,
        export_format="google-merchant",
        retail_markup=3.0,
        min_hot_product_score=40,
        write_summary=False,
    )
    if not products:
        print("No products to feed.")
        return

    with open("google_merchant_feed.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(products)} feed rows to google_merchant_feed.json")
    print("Upload to Google Merchant Center → Products → Feeds.")
    print("Tip: schedule a daily Apify run + Google scheduled fetch ",
          "for fresh prices.")


if __name__ == "__main__":
    main()
