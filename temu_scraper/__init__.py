"""
Temu Product Scraper — Python SDK

Official Python client for the apivault_labs/temu-product-scraper Apify
actor (v1.2). Real-time Temu product scraping with **14 layers of
dropshipping intelligence** — 40+ enrichment fields per product — for
$0.003 per product.

Returns per product:

- Core (Temu): title, price, original price, discount %, rating,
  reviews count, sold count, shop, description, category, shipping,
  availability, main image, image gallery (up to 10), variants
- Price normalizer (USD): `priceUsd`, `originalPriceUsd`, `priceLocal`,
  `currency`, `discountPct`, `savingsUsd` — 10 currencies (USD/EUR/GBP/
  CAD/AUD/JPY/INR/BRL/MXN/PLN) FX-converted to USD
- Sold count parser: `soldCountInt` (10K+ → 10000, 1.2M+ → 1200000),
  `soldCountTier` (viral/hot/warm/cool/cold), `soldCountIsBucket`
- Reviews count parser: `reviewsCountInt`
- Image gallery: `images[]`, `imagesCount`
- Variants extractor: `variants{color, size}`, `variantsCount`,
  `colorOptions`, `sizeOptions`
- Shipping parser: `freeShipping`, `freeShippingThresholdUsd`,
  `shippingDaysMin`, `shippingDaysMax`
- Auto-categorization (15 categories): electronics / fashion_women /
  fashion_men / home_kitchen / home_decor / beauty / baby_kids /
  toys_games / pet_supplies / sports_outdoor / automotive / ...
- **demandScore (0-100)** + `demandTier` (cold/warm/hot/scorching) +
  `demandScoreReasons[]` — composite of sold × rating × reviews ×
  discount aggressiveness
- **Profit margin estimator**: `estimatedRetailUsd`,
  `estimatedGrossProfitUsd`, `estimatedProfitMarginPct`,
  `arbitrage_tier` (low/medium/high/**unicorn** — ≥65 % margin AND
  ≥10K sold)
- **hotProductScore (0-100)** + `hotProductTier` +
  `hotProductReasons[]` — the "should I add this to my Shopify?"
  composite (50 % demand + 25 % margin + bonuses)
- Trend detection: `isTrending` (sold ≥ 10K AND rating ≥ 4.4)
- Risk flags (4): `riskLowReviews`, `riskNewListing`, `riskPoorRating`,
  `riskSeasonal`, `riskCount`
- **outreachLinks**: AliExpress (find supplier), Amazon (competitor
  pricing), eBay, Google Shopping, TikTok (viral content potential),
  YouTube reviews, Pinterest (organic traffic)

Free aggregate KV records on bulk runs:
- **SUMMARY** — avg/median/min/max price, by_category, by_demand_tier,
  by_arbitrage_tier, total units sold, trending count, free-shipping
  count, with-variants count
- **TOP_PRODUCTS** — top 20 products sorted by `hotProductScore` (your
  daily best-dropshipping-picks digest)

Multi-format export: `default` (full JSON) / `shopify-csv` (19-column
ready-to-import row) / `google-merchant` (Google Shopping feed row).

Quick start:

    from temu_scraper import TemuScraperClient

    client = TemuScraperClient(api_token="apify_api_xxxxxx")

    products, summary = client.scrape([
        "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    ])

    for p in client.filter_unicorns(products):
        print(f"{p['title'][:60]:60}  "
              f"{p['estimatedProfitMarginPct']:.0f}% margin  "
              f"{p['soldCountInt']:,} sold")

    # Daily best dropshipping picks digest (free aggregate)
    top = client.get_top_products()
    for prod in (top or {}).get("top_products", [])[:10]:
        print(f"  {prod['hotProductScore']:3}  {prod['title'][:60]}")

See https://github.com/apivault-labs/temu-product-scraper-python for full docs.
"""

from .client import TemuScraperClient
from .exceptions import (
    ActorRunError,
    ActorTimeoutError,
    AuthenticationError,
    TemuScraperError,
)

__version__ = "0.1.0"
__all__ = [
    "TemuScraperClient",
    "TemuScraperError",
    "AuthenticationError",
    "ActorRunError",
    "ActorTimeoutError",
]
