"""
Full dropshipping winners pipeline.

Filters Temu inventory down to **unicorn-tier** picks (≥65 % margin
AND ≥10K sold) with low risk and good photo coverage — the products
worth importing into your Shopify store immediately.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/dropshipping_winners_pipeline.py
"""

from temu_scraper import TemuScraperClient


CANDIDATE_URLS = [
    # In a real workflow you'd seed this from Temu category pages,
    # the TikTok Shop scraper, or your TOP_PRODUCTS digest from the
    # previous run.
    "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    "https://www.temu.com/portable-blender-g-601099528000001.html",
    # ...
]


def main() -> None:
    client = TemuScraperClient()

    # Server-side filter: drop anything below score 50 + require free
    # shipping. Saves the post-processing pass.
    products, _ = client.scrape(
        CANDIDATE_URLS,
        retail_markup=3.0,
        min_hot_product_score=50,
        only_free_shipping=True,
    )
    print(f"After server-side filters: {len(products)} candidates\n")

    # Client-side narrowing — chain the filters
    winners = client.filter_unicorns(products)
    winners = client.filter_low_risk(winners, max_risks=0)
    winners = client.filter_by_min_images(winners, min_images=5)
    winners = client.filter_with_variants(winners)

    # Sort by hotProductScore descending
    winners = sorted(
        winners,
        key=lambda p: -(p.get("hotProductScore") or 0),
    )

    print(f"=== {len(winners)} unicorn-tier winners ===\n")
    for w in winners:
        print(f"  [{w['hotProductScore']:3}] {w['title'][:60]}")
        print(f"    Cost: ${w['priceUsd']:.2f}   "
              f"Suggested retail: ${w['estimatedRetailUsd']:.2f}   "
              f"Margin: {w['estimatedProfitMarginPct']:.0f}%")
        print(f"    Sold: {w['soldCountInt']:,}   "
              f"Rating: {w.get('rating')}★   "
              f"Reviews: {w.get('reviewsCountInt', 0):,}")
        links = w.get("outreachLinks") or {}
        if links.get("aliexpress_search_url"):
            print(f"    Find supplier: {links['aliexpress_search_url']}")
        if links.get("tiktok_search_url"):
            print(f"    Viral check:   {links['tiktok_search_url']}")
        print()


if __name__ == "__main__":
    main()
