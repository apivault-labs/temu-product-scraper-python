"""
TemuScraperClient — synchronous wrapper around the Apify
``apivault_labs/temu-product-scraper`` actor (v1.2).

The actor handles all heavy work on Apify infrastructure:
  - Thunderbit-powered scraping of Temu product pages (no login)
  - 14-layer enrichment: price normalizer (10 currencies + FX),
    sold-count parser, demand score, margin estimator, hot-product
    score, auto-categorization, trend detection, risk flags
  - Server-side filters (`minDemandScore`, `minHotProductScore`,
    `onlyTrending`, `onlyFreeShipping`)
  - Multi-format export (default JSON / shopify-csv / google-merchant)
  - SUMMARY + TOP_PRODUCTS to KV store

This client forwards inputs, polls until the run finishes, then
downloads the dataset and exposes filters & helpers for dropshipping
workflows.

Pricing: $0.003 per product ($3 / 1000). All enrichment included.

Quick start:

    from temu_scraper import TemuScraperClient

    client = TemuScraperClient(api_token="apify_api_xxxxxx")

    products, summary = client.scrape([
        "https://www.temu.com/wireless-bluetooth-earbuds-g-601099527041816.html",
    ])

    for p in client.filter_unicorns(products):
        print(p["title"], p["estimatedProfitMarginPct"], "% margin")
"""

from __future__ import annotations

import os
import time
from typing import Any, Sequence

import requests

from .exceptions import (
    ActorRunError,
    ActorTimeoutError,
    AuthenticationError,
    TemuScraperError,
)


ACTOR_ID = "apivault_labs~temu-product-scraper"
APIFY_API_BASE = "https://api.apify.com/v2"

TERMINAL_OK = {"SUCCEEDED"}
TERMINAL_FAIL = {"FAILED", "TIMED-OUT", "ABORTED"}

PRICE_PER_PRODUCT_USD = 0.003

VALID_EXPORT_FORMATS = ("default", "shopify-csv", "google-merchant")


class TemuScraperClient:
    """Synchronous client for the Temu Product Scraper Apify actor.

    Parameters
    ----------
    api_token : str, optional
        Apify Personal API token. Falls back to ``APIFY_API_TOKEN``.
    timeout : int, optional
        Maximum seconds to wait for an actor run. Default 1200 (20 min) —
        Temu pages are slow (15-30s each); large catalogs can take
        several minutes at the recommended `maxConcurrency=3`.
    poll_interval : float, optional
        Seconds between status polls. Default 3.
    base_url : str, optional
        Override the Apify API base URL.
    """

    def __init__(
        self,
        api_token: str | None = None,
        timeout: int = 1200,
        poll_interval: float = 3.0,
        base_url: str = APIFY_API_BASE,
    ):
        token = api_token or os.environ.get("APIFY_API_TOKEN")
        if not token:
            raise AuthenticationError(
                "Apify API token is required. Pass api_token='apify_api_...' "
                "or set the APIFY_API_TOKEN environment variable. "
                "Get a token at https://console.apify.com/account/integrations"
            )
        self._token = token
        self._timeout = int(timeout)
        self._poll_interval = float(poll_interval)
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "User-Agent": "temu-product-scraper-python/0.1.0",
        })
        self._last_run_id: str | None = None
        self._last_dataset_id: str | None = None
        self._last_kvs_id: str | None = None

    # ------------------------------------------------------------------ public

    def scrape(
        self,
        product_urls: Sequence[str],
        *,
        # Field toggles (all default on)
        extract_title: bool = True,
        extract_price: bool = True,
        extract_original_price: bool = True,
        extract_discount: bool = True,
        extract_rating: bool = True,
        extract_reviews_count: bool = True,
        extract_sold_count: bool = True,
        extract_shop: bool = True,
        extract_description: bool = True,
        extract_category: bool = True,
        extract_shipping: bool = True,
        extract_availability: bool = True,
        extract_image: bool = True,
        extract_images: bool = True,
        extract_variants: bool = True,
        extract_enrichment: bool = True,
        extract_outreach_links: bool = True,
        # Margin assumptions
        retail_markup: float = 3.0,
        # Server-side filters
        min_demand_score: int = 0,
        min_hot_product_score: int = 0,
        only_trending: bool = False,
        only_free_shipping: bool = False,
        # Export
        export_format: str = "default",
        write_summary: bool = True,
        top_products_n: int = 20,
        # Plumbing
        thunderbit_retries: int = 1,
        max_concurrency: int = 3,
        timeout_per_product: int = 180,
        actor_timeout_secs: int = 1800,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Scrape Temu products and return enriched results.

        Parameters
        ----------
        product_urls : Sequence[str]
            Full Temu product URLs
            (``https://www.temu.com/<slug>-g-<id>.html``) or bare numeric
            product IDs. Mix freely.
        retail_markup : float, optional
            Markup applied to Temu cost to estimate retail price.
            Default 3.0 (industry standard for Amazon/Shopify
            dropshipping). Lower for eBay/Mercari (1.8-2.2). Higher for
            niche/branded (4.0-6.0).
        min_demand_score : int, optional
            Drop products below this demand score (0-100).
        min_hot_product_score : int, optional
            Drop products below this hot-product score (0-100). Set ≥55
            for a premium-only catalog.
        only_trending : bool, optional
            Keep only products with ``isTrending = true``
            (sold ≥ 10K AND rating ≥ 4.4).
        only_free_shipping : bool, optional
            Keep only products with free shipping (max margin for
            dropshippers).
        export_format : str, optional
            ``default`` (full JSON, all 40+ fields) /
            ``shopify-csv`` (19-column ready-to-import row) /
            ``google-merchant`` (Google Shopping feed row).
        write_summary : bool, optional
            Write SUMMARY + TOP_PRODUCTS records to the run's KV store.
        top_products_n : int, optional
            How many top products to include in TOP_PRODUCTS (5-100).

        Returns
        -------
        tuple[list[dict], dict | None]
            ``(products, summary)`` — ``summary`` is the SUMMARY KV
            record or ``None`` if ``write_summary`` was disabled.
        """
        if not product_urls:
            raise ValueError("product_urls must be a non-empty sequence")

        cleaned_urls = [str(u).strip() for u in product_urls if str(u).strip()]
        if not cleaned_urls:
            raise ValueError("product_urls is empty after cleaning")

        if export_format not in VALID_EXPORT_FORMATS:
            raise ValueError(
                f"export_format must be one of {VALID_EXPORT_FORMATS}, "
                f"got {export_format!r}"
            )

        try:
            markup = float(retail_markup)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"retail_markup must be numeric, got {retail_markup!r}"
            ) from e
        if markup <= 0:
            raise ValueError(f"retail_markup must be > 0, got {markup}")

        payload = {
            "productUrls": cleaned_urls,
            "extractTitle": bool(extract_title),
            "extractPrice": bool(extract_price),
            "extractOriginalPrice": bool(extract_original_price),
            "extractDiscount": bool(extract_discount),
            "extractRating": bool(extract_rating),
            "extractReviewsCount": bool(extract_reviews_count),
            "extractSoldCount": bool(extract_sold_count),
            "extractShop": bool(extract_shop),
            "extractDescription": bool(extract_description),
            "extractCategory": bool(extract_category),
            "extractShipping": bool(extract_shipping),
            "extractAvailability": bool(extract_availability),
            "extractImage": bool(extract_image),
            "extractImages": bool(extract_images),
            "extractVariants": bool(extract_variants),
            "extractEnrichment": bool(extract_enrichment),
            "extractOutreachLinks": bool(extract_outreach_links),
            "retailMarkup": f"{markup}",
            "minDemandScore": max(0, min(100, int(min_demand_score))),
            "minHotProductScore": max(0, min(100, int(min_hot_product_score))),
            "onlyTrending": bool(only_trending),
            "onlyFreeShipping": bool(only_free_shipping),
            "exportFormat": export_format,
            "writeSummary": bool(write_summary),
            "topProductsN": max(5, min(100, int(top_products_n))),
            "thunderbitRetries": max(0, min(3, int(thunderbit_retries))),
            "maxConcurrency": max(1, min(8, int(max_concurrency))),
            "timeout": max(60, min(300, int(timeout_per_product))),
        }

        run_id = self._start_run(payload, actor_timeout_secs=actor_timeout_secs)
        run = self._wait_for_run(run_id)
        self._last_run_id = run_id
        self._last_dataset_id = run.get("defaultDatasetId")
        self._last_kvs_id = run.get("defaultKeyValueStoreId")
        records = self._fetch_dataset(self._last_dataset_id)

        summary = None
        if write_summary and self._last_kvs_id:
            summary = self._fetch_kv_record(self._last_kvs_id, "SUMMARY")

        return records, summary

    def scrape_one(
        self,
        product_url: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Convenience wrapper to scrape a single product URL.

        Returns the first record or ``None`` if the actor returned an
        empty dataset. All keyword arguments forward to
        :meth:`scrape`.
        """
        # Smaller defaults for single-product runs
        kwargs.setdefault("write_summary", False)
        kwargs.setdefault("max_concurrency", 1)
        records, _ = self.scrape([product_url], **kwargs)
        return records[0] if records else None

    # ------------------------------------------------------------------ KV helpers

    def get_summary(self) -> dict[str, Any] | None:
        """Fetch the aggregate ``SUMMARY`` record from the most recent run."""
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(self._last_kvs_id, "SUMMARY")

    def get_top_products(self) -> dict[str, Any] | None:
        """Fetch the ``TOP_PRODUCTS`` snapshot from the most recent run.

        Top N products sorted by ``hotProductScore`` — your daily
        best-dropshipping-picks digest. Each entry includes a slim
        copy of the full product record with the key actionable
        fields (title, score, margin, sold count, outreach links).
        """
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(self._last_kvs_id, "TOP_PRODUCTS")

    # ------------------------------------------------------------------ filters

    def filter_by_demand_tier(
        self,
        products: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter to products whose ``demandTier`` is in the requested set.

        Tiers: ``cold`` / ``warm`` / ``hot`` / ``scorching``. Default
        keeps ``("scorching", "hot")``.
        """
        if not tiers:
            tiers = ("scorching", "hot")
        wanted = {t.lower() for t in tiers}
        return [
            p for p in products
            if (p.get("demandTier") or "").lower() in wanted
        ]

    def filter_by_hot_product_tier(
        self,
        products: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``hotProductTier`` (cold/warm/hot/scorching)."""
        if not tiers:
            tiers = ("scorching", "hot")
        wanted = {t.lower() for t in tiers}
        return [
            p for p in products
            if (p.get("hotProductTier") or "").lower() in wanted
        ]

    def filter_by_arbitrage_tier(
        self,
        products: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``arbitrage_tier`` (low/medium/high/unicorn).

        Default keeps ``("unicorn", "high")`` — best dropshipping picks.
        """
        if not tiers:
            tiers = ("unicorn", "high")
        wanted = {t.lower() for t in tiers}
        return [
            p for p in products
            if (p.get("arbitrage_tier") or "").lower() in wanted
        ]

    def filter_unicorns(
        self,
        products: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to **unicorn**-tier products (≥65 % margin AND
        ≥10K sold) — the highest-conviction dropshipping picks.
        """
        return self.filter_by_arbitrage_tier(products, "unicorn")

    def filter_trending(
        self,
        products: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to products flagged as ``isTrending`` (sold ≥ 10K AND
        rating ≥ 4.4)."""
        return [p for p in products if p.get("isTrending")]

    def filter_free_shipping(
        self,
        products: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to products with free shipping — best dropshipper margin."""
        return [p for p in products if p.get("freeShipping")]

    def filter_by_category(
        self,
        products: Sequence[dict[str, Any]],
        *categories: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``autoCategory`` (electronics/fashion_women/
        fashion_men/home_kitchen/home_decor/beauty/baby_kids/toys_games/
        pet_supplies/sports_outdoor/automotive/...)."""
        if not categories:
            return list(products)
        wanted = {c.lower() for c in categories}
        return [
            p for p in products
            if (p.get("autoCategory") or "").lower() in wanted
        ]

    def filter_by_min_margin(
        self,
        products: Sequence[dict[str, Any]],
        min_pct: float,
    ) -> list[dict[str, Any]]:
        """Keep only products whose ``estimatedProfitMarginPct`` is at
        least ``min_pct``."""
        return [
            p for p in products
            if (p.get("estimatedProfitMarginPct") or 0) >= min_pct
        ]

    def filter_by_min_sold(
        self,
        products: Sequence[dict[str, Any]],
        min_units: int,
    ) -> list[dict[str, Any]]:
        """Keep only products that have sold at least ``min_units``."""
        return [
            p for p in products
            if (p.get("soldCountInt") or 0) >= min_units
        ]

    def filter_by_min_rating(
        self,
        products: Sequence[dict[str, Any]],
        min_rating: float,
    ) -> list[dict[str, Any]]:
        """Keep only products with rating ≥ ``min_rating``."""
        return [
            p for p in products
            if (p.get("rating") or 0) >= min_rating
        ]

    def filter_by_price_range(
        self,
        products: Sequence[dict[str, Any]],
        min_usd: float = 0.0,
        max_usd: float | None = None,
    ) -> list[dict[str, Any]]:
        """Keep only products whose ``priceUsd`` falls in the range."""
        out: list[dict[str, Any]] = []
        for p in products:
            price = p.get("priceUsd")
            if price is None:
                continue
            if price < min_usd:
                continue
            if max_usd is not None and price > max_usd:
                continue
            out.append(p)
        return out

    def filter_low_risk(
        self,
        products: Sequence[dict[str, Any]],
        max_risks: int = 0,
    ) -> list[dict[str, Any]]:
        """Filter to products with at most ``max_risks`` flagged risks.

        Risk flags: ``riskLowReviews``, ``riskNewListing``,
        ``riskPoorRating``, ``riskSeasonal``.
        """
        return [
            p for p in products
            if (p.get("riskCount") or 0) <= max_risks
        ]

    def filter_with_variants(
        self,
        products: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to products with at least one variant (color or size).

        Useful for Shopify migration where you want full variant
        coverage out of the gate.
        """
        return [
            p for p in products
            if (p.get("variantsCount") or 0) > 0
        ]

    def filter_by_min_images(
        self,
        products: Sequence[dict[str, Any]],
        min_images: int,
    ) -> list[dict[str, Any]]:
        """Keep only products with at least ``min_images`` photos.

        High-photo-count products convert better on Shopify/Amazon —
        recommend ``min_images=5``.
        """
        return [
            p for p in products
            if (p.get("imagesCount") or 0) >= min_images
        ]

    # ------------------------------------------------------------------ helpers

    def estimate_cost(self, expected_products: int) -> float:
        """Estimate USD cost for ``expected_products`` products at
        $3 / 1000.

        Use this *before* calling :meth:`scrape` to budget your run.
        """
        return round(expected_products * PRICE_PER_PRODUCT_USD, 4)

    def deduplicate_across_runs(
        self,
        previous_products: Sequence[dict[str, Any]],
        new_products: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Drop products from ``new_products`` whose ``productId`` was
        already in ``previous_products``. Useful for daily monitoring
        loops where you want to track only newly-added Temu listings.
        """
        seen = {
            p.get("productId")
            for p in previous_products
            if p.get("productId")
        }
        return [
            p for p in new_products
            if p.get("productId") and p["productId"] not in seen
        ]

    # ------------------------------------------------------------------ private

    def _start_run(
        self,
        payload: dict[str, Any],
        actor_timeout_secs: int,
    ) -> str:
        url = f"{self._base_url}/acts/{ACTOR_ID}/runs"
        params = {"timeout": int(actor_timeout_secs)}
        try:
            r = self._session.post(url, params=params, json=payload, timeout=30)
        except requests.RequestException as e:
            raise TemuScraperError(f"Failed to start actor run: {e}") from e
        if r.status_code == 401:
            raise AuthenticationError(
                "Apify rejected the API token. Generate a new one at "
                "https://console.apify.com/account/integrations"
            )
        if r.status_code >= 400:
            raise ActorRunError(
                f"Apify returned HTTP {r.status_code} when starting run: "
                f"{r.text[:300]}"
            )
        data = r.json().get("data") or {}
        run_id = data.get("id")
        if not run_id:
            raise ActorRunError(f"Apify response missing run id: {r.text[:300]}")
        return run_id

    def _wait_for_run(self, run_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/actor-runs/{run_id}"
        deadline = time.time() + self._timeout
        while True:
            try:
                r = self._session.get(url, timeout=30)
            except requests.RequestException as e:
                raise TemuScraperError(f"Failed to poll run status: {e}") from e
            if r.status_code >= 400:
                raise ActorRunError(
                    f"Apify returned HTTP {r.status_code} when polling: "
                    f"{r.text[:300]}"
                )
            run = r.json().get("data") or {}
            status = run.get("status")
            if status in TERMINAL_OK:
                return run
            if status in TERMINAL_FAIL:
                raise ActorRunError(
                    f"Actor run {run_id} ended with status={status}: "
                    f"{run.get('statusMessage') or '(no message)'}"
                )
            if time.time() > deadline:
                raise ActorTimeoutError(
                    f"Actor run {run_id} did not finish within "
                    f"{self._timeout}s (last status={status}). Increase "
                    "`timeout=` or fetch the dataset manually."
                )
            time.sleep(self._poll_interval)

    def _fetch_dataset(self, dataset_id: str) -> list[dict[str, Any]]:
        url = f"{self._base_url}/datasets/{dataset_id}/items"
        params = {"clean": "true", "format": "json"}
        try:
            r = self._session.get(url, params=params, timeout=120)
        except requests.RequestException as e:
            raise TemuScraperError(f"Failed to download dataset: {e}") from e
        if r.status_code >= 400:
            raise ActorRunError(
                f"Apify returned HTTP {r.status_code} when fetching "
                f"dataset: {r.text[:300]}"
            )
        try:
            data = r.json()
        except ValueError as e:
            raise ActorRunError(f"Apify dataset is not valid JSON: {e}") from e
        if not isinstance(data, list):
            raise ActorRunError(
                f"Unexpected dataset payload: {type(data).__name__}"
            )
        return data

    def _fetch_kv_record(self, kvs_id: str, key: str) -> dict[str, Any] | None:
        url = f"{self._base_url}/key-value-stores/{kvs_id}/records/{key}"
        try:
            r = self._session.get(url, timeout=30)
        except requests.RequestException:
            return None
        if r.status_code >= 400:
            return None
        try:
            return r.json()
        except ValueError:
            return None
