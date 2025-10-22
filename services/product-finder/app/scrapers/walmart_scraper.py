# services/product-finder/app/scrapers/walmart_scraper.py
from .base_scraper import BaseScraper
import re
import logging
import random

logger = logging.getLogger('walmart_scraper')

class WalmartScraper(BaseScraper):
    def __init__(self, **kwargs):
        # Define user agents before calling parent class constructor
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0'
        ]
        super().__init__(use_selenium=False, **kwargs)  # keep requests-only for now
        self.base_url = "https://www.walmart.com"

    # --- helpers -------------------------------------------------------------

    def _first_image_src(self, node):
        for attr in ("src", "data-src", "data-image-src"):
            v = node.get(attr)
            if v and v.strip():
                return v
        return None

    def _extract_price(self, node):
        """
        Try multiple nodes; if still nothing, regex over the node text.
        """
        # candidate nodes where prices often live
        price_nodes = []
        for sel in [
            "[data-automation-id='product-price']",
            ".price-main",
            ".w_iUH",         # occasional class used by wm
            ".w_mn",
        ]:
            found = node.select_one(sel)
            if found:
                price_nodes.append(found)

        # try candidates
        for n in price_nodes:
            text = n.get_text(" ", strip=True)
            # look for 12.34 or $12.34 patterns
            m = re.search(r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})|\d+(?:\.\d{2})?)', text)
            if m:
                try:
                    return float(m.group(1).replace(",", ""))
                except Exception:
                    pass

        # fallback: scan all text inside node
        text = node.get_text(" ", strip=True)
        m = re.search(r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})|\d+(?:\.\d{2})?)', text)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except Exception:
                return None
        return None

    # --- main ---------------------------------------------------------------

    def search_products(self, query, limit=5):
        """Search for products on Walmart"""
        search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
        logger.info(f"Searching Walmart for: {query}")

        html = self.get_page_content(search_url)
        if not html:
            logger.warning(f"Failed to get content from Walmart for query: {query}")
            # keep your fake fallback
            return self.generate_fake_products(query, limit=limit, source="walmart")

        soup = self.parse_html(html)
        if not soup:
            return self.generate_fake_products(query, limit=limit, source="walmart")

        products = []

        # Walmart changes a lot—try a handful of resilient containers
        selectors = [
            "[data-testid='list-view'] [data-item-id]",
            "[data-automation-id='product']",
            "[data-testid='product-card']",
            "div.mb1.ph1.pa0-xl.bb.b--near-white",
            ".search-result-gridview-items .search-result-gridview-item",
        ]

        results = []
        for sel in selectors:
            results = soup.select(sel)
            if results:
                logger.info(f"Found {len(results)} Walmart nodes with selector: {sel}")
                break

        # fallback: try generic “card-like” divs with an <a> and an <img> inside
        if not results:
            all_divs = soup.find_all("div")
            for d in all_divs:
                if d.find("a") and d.find("img"):
                    results.append(d)
                    if len(results) >= limit * 3:
                        break
            if results:
                logger.info(f"Found {len(results)} generic candidate nodes")

        for node in results:
            if len(products) >= limit:
                break

            product = {"source": "walmart", "category": query}

            # title (try multiple selectors)
            title = None
            for sel in [
                "[data-testid='product-title']",
                "a.product-title-link",
                "span.lh-title",
                "span.ellipse-2",
            ]:
                el = node.select_one(sel)
                if el and el.get_text(strip=True):
                    title = el.get_text(strip=True)
                    break

            # generic title fallback: any long-ish span that’s not obviously a price
            if not title:
                for span in node.find_all("span"):
                    t = span.get_text(" ", strip=True)
                    if t and len(t) > 15 and "$" not in t:
                        title = t
                        break

            if not title:
                continue  # must have a title
            product["title"] = title

            # price (optional)
            price = self._extract_price(node)
            if price is not None:
                product["price"] = price

            # image
            img_url = None
            for sel in [
                "img[data-testid='product-image']",
                "img.product-image",
                "img",  # generic last resort
            ]:
                el = node.select_one(sel)
                if el:
                    img_url = self._first_image_src(el)
                    if img_url:
                        break
            if img_url:
                product["image"] = img_url

            # url
            url = None
            for sel in [
                "a[link-identifier='linkText']",
                "a.product-title-link",
                "a[href]",
            ]:
                el = node.select_one(sel)
                if el and el.get("href"):
                    href = el["href"]
                    url = href if href.startswith("http") else f"{self.base_url}{href}"
                    break
            product["url"] = url or search_url

            # description (basic)
            product["description"] = product["title"]

            # only append if we have at least title (+ url is nice to have)
            products.append(product)

        # keep YOUR fake fallback:
        if not products and query:
            logger.warning(f"No Walmart products found for query: {query}. Generating mock products.")
            products = self.generate_fake_products(query, limit=limit, source="walmart")

        return products
