"""
Daily monitoring loop with cross-run dedup.

Schedule this script daily (cron / GitHub Actions / Windows Task
Scheduler). It only charges for **newly listed** Temu products by
deduplicating against the previous run's `productId` set. Keeps your
catalog fresh without re-paying for unchanged listings.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/daily_monitoring.py
"""

from __future__ import annotations

import json
from pathlib import Path

from temu_scraper import TemuScraperClient


WATCHED_URLS = [
    "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    # ...add the URLs of category pages or competitor listings here
]
STATE_FILE = Path("temu_monitor_state.json")


def main() -> None:
    client = TemuScraperClient()

    previous: list[dict] = []
    if STATE_FILE.exists():
        previous = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    today, summary = client.scrape(
        WATCHED_URLS,
        retail_markup=3.0,
        only_free_shipping=False,
    )

    new_listings = client.deduplicate_across_runs(previous, today)
    print(f"Today: {len(today)} total, "
          f"{len(new_listings)} brand-new since last run")

    # Show the freshest unicorn-tier picks
    fresh_unicorns = client.filter_unicorns(new_listings)
    if fresh_unicorns:
        print(f"\n=== {len(fresh_unicorns)} fresh unicorns ===")
        for u in fresh_unicorns[:10]:
            print(f"  [{u.get('hotProductScore', 0):3}] "
                  f"{u['title'][:60]}")
            print(f"    margin {u['estimatedProfitMarginPct']:.0f}%, "
                  f"sold {u['soldCountInt']:,}")

    # Persist all of today's productIds so tomorrow's run can dedup
    STATE_FILE.write_text(
        json.dumps(today, ensure_ascii=False),
        encoding="utf-8",
    )

    if summary:
        print(f"\nTrending products today: "
              f"{summary.get('trending_count', 0)}")


if __name__ == "__main__":
    main()
