# 🛒 Temu Product Scraper — Python SDK

[![PyPI version](https://img.shields.io/badge/pip-temu--product--scraper-blue.svg)](https://github.com/apivault-labs/temu-product-scraper-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/apivault-labs/temu-product-scraper-python/actions/workflows/ci.yml/badge.svg)](https://github.com/apivault-labs/temu-product-scraper-python/actions/workflows/ci.yml)

> **40+ enrichment fields per Temu product. $0.003 each. Shopify-CSV
> ready. Profit-margin estimator + unicorn detector built in. No login
> required.**

Direct alternative to **Sell The Trend / Ecomhunt / Niche Scraper**
($30-100/mo subscriptions) for use cases the official APIs can't
cover: USD-normalized prices across 10 currencies, parsed sold counts
(`10K+` → `10000`), demand score 0-100, profit margin estimator with
arbitrage tier (low/medium/high/**unicorn**), 15-category auto-tagging,
trend detection, risk flags, and one-click research links to
AliExpress / Amazon / TikTok / Pinterest.

```bash
pip install git+https://github.com/apivault-labs/temu-product-scraper-python
```

```python
from temu_scraper import TemuScraperClient

client = TemuScraperClient(api_token="apify_api_xxxxxx")

products, summary = client.scrape([
    "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    "https://www.temu.com/portable-blender-g-601099528000001.html",
])

# The unicorns: ≥65% margin AND ≥10K sold
for p in client.filter_unicorns(products):
    print(f"{p['title'][:60]:60}  "
          f"{p['estimatedProfitMarginPct']:.0f}% margin  "
          f"{p['soldCountInt']:,} sold")
```

## What you get for $0.003 per product

For every Temu product analyzed, you get **40+ structured fields** —
core product data plus **14 derived enrichment layers**.

### ⭐ Core (Temu)

- `title`, `priceText`, `originalPriceText`, `discountPct`
- `rating`, `reviewsCountText`, `soldCountText`
- `shopName`, `description`, `category`
- `shippingInfo`, `availability`
- `imageUrl` (main), `images[]` (gallery up to 10), `variants{}`

### 💵 Price normalizer (USD-converted)

- `priceUsd`, `originalPriceUsd`, `priceLocal`, `currency`
- 10 currencies recognized: USD/EUR/GBP/CAD/AUD/JPY/INR/BRL/MXN/PLN
- FX-converted to USD using mid-market rates
- `discountPct`, `savingsUsd`
- Handles US (`$1,234.56`) and EU (`€1.234,56`) thousand-separator styles

### 🔥 Sold count parser (Temu's signature metric)

- `soldCountInt` — `10K+` → `10000`, `1.2M+` → `1200000`
- `soldCountTier` — `viral` / `hot` / `warm` / `cool` / `cold`
- `soldCountIsBucket` — flag when value was a "+" approximation

### ⭐ Reviews count parser

- `reviewsCountInt` — same K/M/+ parsing

### 📦 Image gallery

- `images[]` — list of all product images parsed from "All Images"
- `imagesCount` — needed for full Shopify CSV migration

### 🎨 Variants extractor

- `variants{}` — `{color: ['Red', 'Blue'], size: ['S', 'M', 'L']}`
- `variantsCount`, `colorOptions`, `sizeOptions`

### 🚚 Shipping parser

- `freeShipping` boolean
- `freeShippingThresholdUsd` (e.g. `$35` free shipping threshold)
- `shippingDaysMin`, `shippingDaysMax`

### 🏷️ Auto-categorization (15 categories)

`electronics` / `fashion_women` / `fashion_men` / `fashion_unisex` /
`home_kitchen` / `home_decor` / `home_garden` / `beauty` / `baby_kids` /
`toys_games` / `pet_supplies` / `sports_outdoor` / `automotive` /
`office_school` / `tools_hardware`

### 📊 **demandScore (0-100)** + tier + reasons

Composite of sold count × rating × reviews × discount aggressiveness:

- `demandTier` — `cold` / `warm` / `hot` / `scorching`
- `demandScoreReasons[]` — explainable signals
  (e.g. `"50,000+ sold (hot)"`, `"4.8★ exceptional"`,
  `"-56% discount on volume mover"`)

### 💰 **Profit margin estimator**

Assumes retail = Temu cost × markup (configurable via `retail_markup`,
default `3.0`):

- `estimatedRetailUsd` — suggested Shopify/Amazon price
- `estimatedGrossProfitUsd`, `estimatedProfitMarginPct`
- `arbitrage_tier` — `low` / `medium` / `high` / **`unicorn`**
- **Unicorn = ≥65 % margin AND ≥10K sold** — best dropshipping picks

### 🎯 **hotProductScore (0-100)** + tier + reasons

The "should I add this to my Shopify?" composite — combines demand,
margin, free shipping, photos, variants, and risk penalties:

- `hotProductTier` — `cold` / `warm` / `hot` / `scorching`
- `hotProductReasons[]` — explainable signals
  (e.g. `"high demand (85)"`, `"66% margin"`, `"variants available"`)

### 🚀 Trend detection

- `isTrending` — sold ≥ 10K AND rating ≥ 4.4

### ⚠️ Risk flags (4)

- `riskLowReviews` — < 50 reviews (unverified product)
- `riskNewListing` — < 100 sold + < 20 reviews (might be flop)
- `riskPoorRating` — rating < 3.5
- `riskSeasonal` — seasonal keyword in title (christmas/halloween/...)
- `riskCount` — total risk count

### 📞 One-click research links

- `aliexpress_search_url` — find original supplier (often cheaper than Temu)
- `amazon_search_url` — check competitor pricing
- `ebay_search_url`, `google_shopping_url`
- `tiktok_search_url` — viral content potential
- `youtube_review_search_url` — `"[product] review"`
- `pinterest_search_url` — organic-traffic potential

### 📊 Free aggregate KV records on bulk runs

**SUMMARY** — avg/median/min/max price, by_category, by_demand_tier,
by_arbitrage_tier, total units sold across run, trending count,
free-shipping count, with-variants count.

**TOP_PRODUCTS** — top 20 products sorted by `hotProductScore`
(your daily best-dropshipping-picks digest). Read with:

```python
top = client.get_top_products()
for prod in top["top_products"][:10]:
    print(prod["hotProductScore"], prod["title"])
```

## Sample output

```json
{
  "success": true,
  "productUrl": "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
  "productId": "601099527041816",
  "title": "Wireless Bluetooth Earbuds with Charging Case",
  "shopName": "TopTech Store",
  "category": "Electronics > Audio > Earbuds",
  "autoCategory": "electronics",

  "priceText": "US$10.99",
  "priceUsd": 10.99,
  "currency": "USD",
  "originalPriceUsd": 24.99,
  "discountPct": 56,
  "savingsUsd": 14.00,

  "rating": 4.8,
  "soldCountText": "50K+",
  "soldCountInt": 50000,
  "soldCountTier": "hot",
  "reviewsCountInt": 12000,

  "freeShipping": true,
  "freeShippingThresholdUsd": 10,
  "shippingDaysMin": 5,
  "shippingDaysMax": 12,

  "images": [
    "https://img.temu.com/o/abc.jpg",
    "https://img.temu.com/o/def.jpg"
  ],
  "imagesCount": 8,
  "variants": {
    "color": ["Black", "White", "Blue"],
    "size": ["Standard"]
  },
  "variantsCount": 4,

  "demandScore": 85,
  "demandTier": "scorching",
  "demandScoreReasons": [
    "50,000+ sold (hot)",
    "4.8★ exceptional",
    "12,000+ reviews",
    "-56% discount on volume mover"
  ],

  "estimatedRetailUsd": 32.97,
  "estimatedGrossProfitUsd": 21.98,
  "estimatedProfitMarginPct": 66.7,
  "arbitrage_tier": "unicorn",
  "assumedMarkup": 3.0,

  "hotProductScore": 88,
  "hotProductTier": "scorching",
  "hotProductReasons": [
    "high demand (85)",
    "66% margin",
    "free shipping",
    "good photos",
    "variants available"
  ],

  "isTrending": true,
  "riskLowReviews": false,
  "riskNewListing": false,
  "riskCount": 0,

  "outreachLinks": {
    "aliexpress_search_url": "https://www.aliexpress.com/wholesale?SearchText=Wireless+Bluetooth+Earbuds+with+Charging+Case",
    "amazon_search_url": "https://www.amazon.com/s?k=Wireless+Bluetooth+Earbuds+with+Charging+Case",
    "tiktok_search_url": "https://www.tiktok.com/search?q=Wireless+Bluetooth+Earbuds+with+Charging+Case",
    "youtube_review_search_url": "https://www.youtube.com/results?search_query=Wireless+Bluetooth+Earbuds+review"
  }
}
```

## Use cases

### 🥇 Dropshipping winners pipeline

```python
# Find unicorn-tier picks (≥65% margin AND ≥10K sold) ready for Shopify
products, _ = client.scrape(URLS,
                            retail_markup=3.0,
                            min_hot_product_score=50,
                            only_free_shipping=True)

winners = client.filter_unicorns(products)
winners = client.filter_low_risk(winners, max_risks=0)
winners = client.filter_by_min_images(winners, min_images=5)

for w in sorted(winners, key=lambda p: -p["hotProductScore"]):
    print(f"[{w['hotProductScore']:3}] {w['title'][:60]}")
    print(f"  margin {w['estimatedProfitMarginPct']:.0f}%, "
          f"sold {w['soldCountInt']:,}")
```

### 💰 Shopify migration (one-click)

```python
# export_format="shopify-csv" returns 19-column rows ready to import
products, _ = client.scrape(URLS, export_format="shopify-csv")
# → write to .csv, upload at Shopify Admin → Products → Import
```

### 🛍️ Google Shopping ads feed

```python
products, _ = client.scrape(URLS, export_format="google-merchant")
# → JSON rows ready to drop into Google Merchant Center
```

### 📈 Trend spotting / daily digest

```python
# Daily monitoring with cross-run dedup — only charge for new listings
today, summary = client.scrape(WATCHED_URLS)
new_listings = client.deduplicate_across_runs(yesterday, today)
fresh_unicorns = client.filter_unicorns(new_listings)
```

### 🔍 Niche category research

```python
# Pet supplies sweet-spot pricing
products, summary = client.scrape(SEED_URLS)
in_niche = client.filter_by_category(products, "pet_supplies")
in_niche = client.filter_by_min_rating(in_niche, 4.0)
in_niche = client.filter_by_min_sold(in_niche, 1000)
```

### ⚠️ Risk audit before bulk import

```python
# Drop products with any risk flag before adding to your store
catalog = client.filter_low_risk(products, max_risks=0)
```

### 🏪 Amazon arbitrage research

```python
# Compare Temu cost to Amazon retail
for p in products:
    amazon_url = p["outreachLinks"]["amazon_search_url"]
    print(f"Temu ${p['priceUsd']:.2f} vs Amazon → {amazon_url}")
```

## Pricing

| Volume | Cost |
|---|---|
| 1 product | $0.003 |
| 100 | $0.30 |
| 1,000 | $3.00 |
| 10,000 | $30.00 |

```python
client.estimate_cost(2_500)   # 7.5 USD
```

The Apify free tier ($5 credit) covers ~1,650 products. Pay only for
successfully scraped products — failed pages don't trigger
pay-per-event charging.

## Installation

```bash
pip install git+https://github.com/apivault-labs/temu-product-scraper-python
```

Or pin to a release tag:

```bash
pip install git+https://github.com/apivault-labs/temu-product-scraper-python@v0.1.0
```

## Setup

1. Create an Apify account: <https://console.apify.com/sign-up>
2. Get your API token: <https://console.apify.com/account/integrations>
3. Either pass it explicitly or export `APIFY_API_TOKEN`:

```bash
export APIFY_API_TOKEN="apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

```python
client = TemuScraperClient()                        # picks up env var
client = TemuScraperClient(api_token="apify_...")   # explicit
```

## Examples

| File | What it shows |
|---|---|
| [`examples/quickstart.py`](examples/quickstart.py) | Single product with full enrichment breakdown |
| [`examples/bulk_scrape.py`](examples/bulk_scrape.py) | Multi-product run + SUMMARY/TOP_PRODUCTS |
| [`examples/dropshipping_winners_pipeline.py`](examples/dropshipping_winners_pipeline.py) | Full unicorn-finder workflow |
| [`examples/shopify_csv_migration.py`](examples/shopify_csv_migration.py) | One-click Shopify import flow |
| [`examples/google_merchant_feed.py`](examples/google_merchant_feed.py) | Google Shopping ads feed export |
| [`examples/daily_monitoring.py`](examples/daily_monitoring.py) | Cross-run dedup with `productId` |
| [`examples/niche_category_research.py`](examples/niche_category_research.py) | Deep dive into a single category |
| [`examples/export_to_csv.py`](examples/export_to_csv.py) | Flat CSV for spreadsheet analysis |

## API reference

### `TemuScraperClient(api_token=None, timeout=1200, poll_interval=3.0)`

### `scrape(product_urls, **kwargs) -> (products, summary)`

Forwards all 26 actor input flags. See full list in
[`temu_scraper/client.py`](temu_scraper/client.py).

Key parameters: `retail_markup` (default 3.0), `min_demand_score`,
`min_hot_product_score`, `only_trending`, `only_free_shipping`,
`export_format` (default/shopify-csv/google-merchant), `write_summary`,
`top_products_n`, `max_concurrency` (default 3).

### `scrape_one(product_url, **kwargs) -> dict | None`

Convenience wrapper for single-product scrapes. Sets
`write_summary=False` and `max_concurrency=1` by default.

### KV record helpers

- `get_summary() -> dict | None`
- `get_top_products() -> dict | None`

### Filters (return new lists)

- `filter_by_demand_tier(products, *tiers)` — cold/warm/hot/scorching
- `filter_by_hot_product_tier(products, *tiers)`
- `filter_by_arbitrage_tier(products, *tiers)` — low/medium/high/unicorn
- `filter_unicorns(products)` — shortcut for arbitrage_tier=unicorn
- `filter_trending(products)` — `isTrending = true`
- `filter_free_shipping(products)`
- `filter_by_category(products, *categories)` — 15 categories
- `filter_by_min_margin(products, min_pct)`
- `filter_by_min_sold(products, min_units)`
- `filter_by_min_rating(products, min_rating)`
- `filter_by_price_range(products, min_usd, max_usd)`
- `filter_low_risk(products, max_risks=0)`
- `filter_with_variants(products)`
- `filter_by_min_images(products, min_images)`

### Helpers

- `estimate_cost(expected_products) -> float`
- `deduplicate_across_runs(previous, new) -> list` — for daily monitoring

## How it works

```
your_code → TemuScraperClient → Apify API
                                    ↓
                            Apify actor v1.2
                                    ↓
                        Thunderbit (Temu data)
                                    ↓
              14-layer enrichment (price/sold/demand/margin/...)
                                    ↓
                        Server-side filters
                                    ↓
                  default JSON / Shopify CSV / Google Merchant
                                    ↓
              + free SUMMARY + TOP_PRODUCTS in KV store
                                    ↓
                          you, in Python
```

## FAQ

**Q: Do I need a Temu account?**
A: No. The actor scrapes public product pages — no login.

**Q: How accurate is `estimatedProfitMarginPct`?**
A: It's a heuristic based on a configurable markup (default 3×, the
industry rule for Amazon/Shopify dropshipping). For eBay/Mercari use
1.8-2.2; for niche/branded stores use 4-6. Set via `retail_markup`.

**Q: How accurate is `soldCountInt`?**
A: Temu shows bucketed values like "10K+", "50K+". The parser converts
these to the lower bound (`10K+` → 10000) and sets
`soldCountIsBucket=true` to flag the approximation.

**Q: Can I get the actual photos for Shopify import?**
A: Yes — `extract_images=True` (default) returns up to 10 image URLs
per product in `images[]`. The Shopify CSV export uses these
automatically.

**Q: Does it work for non-US Temu (eu.temu.com / temu.de)?**
A: Yes — the actor parses prices in 10 currencies (EUR/GBP/CAD/...) and
auto-converts to USD for sortable comparison.

**Q: How is this better than Sell The Trend / Ecomhunt / Niche
Scraper?**
A: Pay-as-you-go ($0.003/product) instead of $30-100/month
subscription. You get raw structured data — no "curated" filter
forcing you into someone else's picks. Plus Shopify CSV and Google
Merchant exports the others charge extra for.

**Q: Will I get blocked / banned?**
A: All scraping happens on Apify infrastructure via Thunderbit's
whitelisted pool. You don't connect to Temu directly — your IP is
never touched.

**Q: Why are some products `success: false`?**
A: Temu is sensitive to aggressive parallelism. Lower
`max_concurrency` to 2-3 (already the default) and rerun. Failed
products are still pushed (with `success: false`) but don't trigger
pay-per-event charging.

**Q: Can I track listings over time?**
A: Yes — see [`examples/daily_monitoring.py`](examples/daily_monitoring.py).
Use `deduplicate_across_runs()` to avoid re-paying for unchanged
listings.

## Keywords

`temu` `temu-scraper` `temu-api` `temu-product-scraper`
`temu-without-login` `temu-without-api-key`
`dropshipping` `dropshipping-tools` `dropshipping-research`
`winning-products` `product-research`
`shopify-import` `shopify-csv` `shopify-csv-import` `shopify-migration`
`google-merchant-feed` `google-shopping-feed`
`ecommerce-scraper` `ecommerce-data` `marketplace-scraper`
`amazon-arbitrage` `ebay-arbitrage` `retail-arbitrage`
`profit-margin-estimator` `competitor-pricing` `price-monitoring`
`niche-scraper-alternative` `sell-the-trend-alternative`
`ecomhunt-alternative` `spocket-alternative`
`trend-detection` `viral-products` `tiktok-shop-research`
`apify` `python-sdk`

## License

MIT — see [LICENSE](LICENSE).
