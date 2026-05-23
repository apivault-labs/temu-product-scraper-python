"""
Quickstart: scrape a single Temu product and print the dropshipping
intelligence breakdown.

    pip install -r requirements.txt
    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/quickstart.py
"""

from temu_scraper import TemuScraperClient


def main() -> None:
    client = TemuScraperClient()  # picks up APIFY_API_TOKEN from env

    product = client.scrape_one(
        "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html"
    )
    if not product or not product.get("success"):
        print("Failed to scrape product:",
              (product or {}).get("error", "no result"))
        return

    print(f"\n=== {product['title']}")
    print(f"  Shop: {product.get('shopName', 'n/a')}")
    print(f"  Auto-category: {product.get('autoCategory', 'n/a')}")
    print()
    print(f"  Price (USD): ${product.get('priceUsd', 0):.2f} "
          f"(was ${product.get('originalPriceUsd', 0):.2f})")
    print(f"  Discount: {product.get('discountPct', 0)}% "
          f"— save ${product.get('savingsUsd', 0):.2f}")
    print(f"  Free shipping: {product.get('freeShipping', False)}")
    print()
    print(f"  Sold: {product.get('soldCountInt', 0):,} "
          f"({product.get('soldCountTier', '?')})")
    print(f"  Reviews: {product.get('reviewsCountInt', 0):,}, "
          f"rating {product.get('rating', 'n/a')}★")
    print(f"  Trending: {product.get('isTrending', False)}")
    print()
    print(f"  Demand: {product.get('demandScore', 0)} "
          f"({product.get('demandTier', '?')})")
    for r in (product.get("demandScoreReasons") or [])[:4]:
        print(f"    + {r}")
    print()
    print(f"  Estimated retail (3× markup): "
          f"${product.get('estimatedRetailUsd', 0):.2f}")
    print(f"  Profit margin: {product.get('estimatedProfitMarginPct', 0):.0f}%")
    print(f"  Arbitrage tier: {product.get('arbitrage_tier', '?')}")
    print()
    print(f"  HOT product score: {product.get('hotProductScore', 0)} "
          f"({product.get('hotProductTier', '?')})")
    for r in (product.get("hotProductReasons") or [])[:5]:
        print(f"    + {r}")
    print()
    print(f"  Risks ({product.get('riskCount', 0)}):")
    for risk in ("riskLowReviews", "riskNewListing",
                 "riskPoorRating", "riskSeasonal"):
        if product.get(risk):
            print(f"    ! {risk}")
    print()
    links = product.get("outreachLinks") or {}
    print("  Validate before importing:")
    if links.get("aliexpress_search_url"):
        print(f"    AliExpress: {links['aliexpress_search_url']}")
    if links.get("amazon_search_url"):
        print(f"    Amazon:     {links['amazon_search_url']}")
    if links.get("tiktok_search_url"):
        print(f"    TikTok:     {links['tiktok_search_url']}")


if __name__ == "__main__":
    main()
