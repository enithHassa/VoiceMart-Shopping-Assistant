import logging
import concurrent.futures
import time
import os

logger = logging.getLogger('scraper_manager')
ALLOW_FAKE = os.getenv("ALLOW_FAKE_PRODUCTS", "true").lower() in ("1", "true", "yes")


class ScraperManager:
    """Manages multiple scrapers and combines their results"""

    def __init__(self, scrapers=None):
        self.scrapers = scrapers or []

    def add_scraper(self, scraper):
        self.scrapers.append(scraper)

    def search_products(self, query, limit=5, sources=None, parallel=True):
        if not query:
            return []

        results = []
        start_time = time.time()

        active_scrapers = [
            s for s in self.scrapers
            if sources is None or s.__class__.__name__.lower().replace("scraper", "") in sources
        ]

        if not active_scrapers:
            logger.warning(f"No scrapers available for query: {query}")
            return []

        def run_scraper(scraper):
            try:
                products = scraper.search_products(query, limit)
                for p in products:
                    self._normalize_product_fields(p)
                logger.info(f"Got {len(products)} products from {scraper.__class__.__name__}")
                return products
            except Exception as e:
                logger.error(f"Error from {scraper.__class__.__name__}: {e}")
                return []

        if parallel:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_scrapers)) as ex:
                futures = {ex.submit(run_scraper, s): s for s in active_scrapers}
                for fut in concurrent.futures.as_completed(futures):
                    results.extend(fut.result())
        else:
            for s in active_scrapers:
                results.extend(run_scraper(s))

        # remove placeholder fake products (if mixing with real)
        if results:
            non_placeholders = [r for r in results if "placehold.co" not in (r.get("image") or r.get("image_url", ""))]
            if non_placeholders:
                results = non_placeholders

        duration = time.time() - start_time
        logger.info(f"Search completed in {duration:.2f}s with {len(results)} total results")
        return results

    def search_by_category(self, category, limit=5, sources=None):
        return self.search_products(category, limit, sources)

    def _normalize_product_fields(self, product):
        if "image" in product and "image_url" not in product:
            product["image_url"] = product["image"]

        required_fields = ["id", "title", "price", "source", "url"]
        for f in required_fields:
            if f not in product:
                if f == "id" and "url" in product:
                    product["id"] = str(hash(product["url"]))
                elif f == "price":
                    product[f] = 0.0
                else:
                    product[f] = f"Unknown {f}"

        # numeric price normalization
        price = product.get("price")
        try:
            product["price"] = float(str(price).replace("$", "").replace(",", ""))
        except Exception:
            product["price"] = 0.0

        return product

    def get_product_details(self, product_url, source=None):
        for scraper in self.scrapers:
            src_name = scraper.__class__.__name__.lower().replace("scraper", "")
            if source is None or src_name == source:
                if scraper.base_url in product_url:
                    return {
                        "url": product_url,
                        "source": src_name,
                        "details": "Product details would go here"
                    }
        return None
