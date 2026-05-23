# Changelog

## [0.1.0] — 2026-05-23

Initial release of the Python SDK for the Temu Product Scraper Apify
actor (v1.2).

### Added

- `TemuScraperClient` with `scrape()` (bulk) and `scrape_one()`
  (single-product convenience wrapper)
- 13 client-side filter helpers:
  - `filter_by_demand_tier(products, *tiers)` —
    cold/warm/hot/scorching
  - `filter_by_hot_product_tier(products, *tiers)`
  - `filter_by_arbitrage_tier(products, *tiers)` —
    low/medium/high/unicorn
  - `filter_unicorns(products)` — ≥65 % margin AND ≥10K sold
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
- KV record helpers: `get_summary()`, `get_top_products()`
- `deduplicate_across_runs()` for daily monitoring loops
  (uses `productId`)
- `estimate_cost(expected_products)` for pre-run budgeting
- All 26 actor input flags exposed as keyword arguments
- 8 example scripts:
  - `quickstart.py`
  - `bulk_scrape.py` with SUMMARY + TOP_PRODUCTS digest
  - `dropshipping_winners_pipeline.py` — full unicorn-finder workflow
  - `shopify_csv_migration.py` — one-click Shopify import flow
  - `google_merchant_feed.py` — Google Shopping ads feed export
  - `daily_monitoring.py` with cross-run dedup
  - `niche_category_research.py` — research a single category deeply
  - `export_to_csv.py` — flat CSV for spreadsheets
- MIT license
