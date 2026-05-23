"""
Bulk-scrape a catalog and read the SUMMARY + TOP_PRODUCTS digest.

The TOP_PRODUCTS aggregate is your daily best-dropshipping-picks
digest — top N products sorted by `hotProductScore`, written
automatically to the run's KV store at no extra cost.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/bulk_scrape.py
"""

from temu_scraper import TemuScraperClient


URLS = [
    "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    "https://www.temu.com/portable-blender-g-601099528000001.html",
    "https://www.temu.com/led-strip-lights-g-601099529000002.html",
    # ...add hundreds more
]


def main() -> None:
    client = TemuScraperClient()

    print(f"Estimated cost: ${client.estimate_cost(len(URLS)):.4f}")

    products, summary = client.scrape(
        URLS,
        retail_markup=3.0,
        write_summary=True,
        top_products_n=20,
    )
    print(f"\nScraped {len(products)} products")

    if summary:
        print("\n=== SUMMARY ===")
        print(f"  By demand tier:    {summary.get('by_demand_tier', {})}")
        print(f"  By arbitrage tier: {summary.get('by_arbitrage_tier', {})}")
        print(f"  By category:       {summary.get('by_category', {})}")
        print(f"  Trending count:    {summary.get('trending_count', 0)}")
        print(f"  Free shipping:     {summary.get('free_shipping_count', 0)}")
        print(f"  With variants:     {summary.get('with_variants_count', 0)}")
        print()
        print(f"  Avg price USD:     ${summary.get('avg_price_usd', 0):.2f}")
        print(f"  Avg margin %:      {summary.get('avg_margin_pct', 0):.1f}%")
        print(f"  Total units sold:  "
              f"{summary.get('total_sold_count', 0):,}")

    top = client.get_top_products()
    if top and top.get("top_products"):
        print("\n=== TOP_PRODUCTS (sorted by hotProductScore) ===")
        for i, prod in enumerate(top["top_products"][:10], 1):
            print(f"\n{i:2}. [{prod.get('hotProductScore', 0):3}] "
                  f"{prod.get('title', '')[:60]}")
            print(f"      ${prod.get('priceUsd', 0):.2f}  "
                  f"margin {prod.get('estimatedProfitMarginPct', 0):.0f}%  "
                  f"sold {prod.get('soldCountInt', 0):,}  "
                  f"({prod.get('arbitrage_tier', '?')})")


if __name__ == "__main__":
    main()
