"""
Deep research on a single niche category.

Pull a chunk of candidate URLs from one auto-category (e.g.
`pet_supplies`) and explore demand + price + margin distribution to
spot the sweet-spot price band before committing to a niche.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/niche_category_research.py
"""

from __future__ import annotations

import statistics

from temu_scraper import TemuScraperClient


CANDIDATE_URLS = [
    # Seed with as many URLs as you can grab from Temu's pet category
    # search results / collection pages — recommend 50-200.
    "https://www.temu.com/cat-self-grooming-brush-g-601099530000003.html",
    "https://www.temu.com/automatic-water-fountain-g-601099530000004.html",
    # ...
]
TARGET_CATEGORY = "pet_supplies"


def main() -> None:
    client = TemuScraperClient()

    products, summary = client.scrape(
        CANDIDATE_URLS,
        retail_markup=3.0,
        write_summary=True,
    )

    # Narrow to the niche — products auto-categorised by the actor
    in_niche = client.filter_by_category(products, TARGET_CATEGORY)
    print(f"In '{TARGET_CATEGORY}': {len(in_niche)}/{len(products)}")

    # Health-check the catalog
    in_niche = client.filter_low_risk(in_niche, max_risks=1)
    in_niche = client.filter_by_min_rating(in_niche, 4.0)
    in_niche = client.filter_by_min_sold(in_niche, 1000)
    print(f"After quality filters: {len(in_niche)}")

    if not in_niche:
        return

    prices = [p.get("priceUsd") for p in in_niche if p.get("priceUsd")]
    margins = [
        p.get("estimatedProfitMarginPct") for p in in_niche
        if p.get("estimatedProfitMarginPct") is not None
    ]
    sold = [p.get("soldCountInt") or 0 for p in in_niche]

    print(f"\n=== {TARGET_CATEGORY.upper()} niche scan ===")
    print(f"  Price USD:  min ${min(prices):.2f}  "
          f"median ${statistics.median(prices):.2f}  "
          f"max ${max(prices):.2f}")
    print(f"  Margin %:   min {min(margins):.0f}%  "
          f"median {statistics.median(margins):.0f}%  "
          f"max {max(margins):.0f}%")
    print(f"  Total sold: {sum(sold):,}")

    print("\nTop 10 unicorns in niche:")
    unicorns = sorted(
        client.filter_unicorns(in_niche),
        key=lambda p: -(p.get("hotProductScore") or 0),
    )[:10]
    for u in unicorns:
        print(f"  [{u['hotProductScore']:3}] {u['title'][:60]}  "
              f"${u['priceUsd']:.2f}  "
              f"{u['estimatedProfitMarginPct']:.0f}% margin")


if __name__ == "__main__":
    main()
