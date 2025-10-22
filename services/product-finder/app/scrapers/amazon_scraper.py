import os
from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger('amazon_scraper')

class AmazonScraper(BaseScraper):
    def __init__(self, **kwargs):
        # Strong UA pool handled by BaseScraper; we still override if needed
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
        ]
        # Allow env to turn Selenium on for Amazon (default ON because of bot protection)
        use_selenium = os.getenv("SCRAPER_USE_SELENIUM_AMAZON", "1") == "1"
        super().__init__(use_selenium=use_selenium, **kwargs)
        self.base_url = "https://www.amazon.com"

    def search_products(self, query, limit=5):
        """Search for products on Amazon"""
        search_url = f"{self.base_url}/s?k={query.replace(' ', '+')}"
        logger.info(f"Searching Amazon for: {query}")

        html = self.get_page_content(search_url)
        if not html:
            logger.warning(f"Failed to get content from Amazon for query: {query}")
            return self.generate_fake_products(query, limit=limit, source="amazon")

        soup = self.parse_html(html)
        if not soup:
            return self.generate_fake_products(query, limit=limit, source="amazon")

        products = []

        # Robust result containers
        result_selectors = [
            "div[data-component-type='s-search-result']",
            "div.s-result-item[data-asin]",
            "div.sg-col-20-of-24.s-result-item",
            "div.rush-component"
        ]

        results = []
        for selector in result_selectors:
            results = soup.select(selector)
            if results:
                # Filter out empty ASINs and sponsored placeholders
                results = [r for r in results if (r.get('data-asin') and r.get('data-asin') != '') or r.select_one("h2")]
                if results:
                    logger.info(f"Found {len(results)} Amazon results using selector: {selector}")
                    break

        for i, item in enumerate(results):
            if i >= limit:
                break

            product = {"source": "amazon", "category": query}

            # ASIN
            asin = item.get('data-asin')
            if asin:
                product['id'] = asin
                product['url'] = f"{self.base_url}/dp/{asin}"

            # Title
            for sel in ["h2 a.a-link-normal span", "h2 a.a-link-normal", "h2 span", ".a-size-medium.a-color-base"]:
                el = item.select_one(sel)
                if el and el.text.strip():
                    product['title'] = el.text.strip()
                    break

            # Price
            for sel in [".a-price .a-offscreen", "span.a-price span.a-offscreen", ".a-price-whole"]:
                el = item.select_one(sel)
                if el:
                    txt = el.text.strip()
                    m = re.search(r'[\d,]+(?:\.\d+)?', txt)
                    if m:
                        product['price'] = float(m.group(0).replace(',', ''))
                        break

            # Image
            for sel in ["img.s-image", ".s-image", "img[data-image-latency='s-product-image']", "img[srcset]"]:
                img = item.select_one(sel)
                if img and img.get('src'):
                    product['image'] = img['src']
                    break

            # URL (fallback if no ASIN)
            if 'url' not in product:
                for sel in ["h2 a.a-link-normal", "a.a-link-normal.s-no-outline", ".a-link-normal.a-text-normal", "a.a-link-normal"]:
                    link = item.select_one(sel)
                    if link and link.get('href'):
                        href = link['href']
                        product['url'] = f"{self.base_url}{href}" if href.startswith('/') else href
                        break
                product.setdefault('url', search_url)

            # Rating (best-effort)
            for sel in [".a-icon-star-small .a-icon-alt", ".a-icon-alt"]:
                rat = item.select_one(sel)
                if rat:
                    txt = getattr(rat, 'text', '') or rat.get('aria-label', '')
                    m = re.search(r'(\d+(\.\d+)?)', txt)
                    if m:
                        product['rating'] = float(m.group(1))
                        break

            # Description
            product['description'] = f"Amazon product: {product.get('title', 'No title available')}"

            if 'title' in product and ('image' in product or 'price' in product):
                products.append(product)

        if not products and query:
            logger.warning(f"No Amazon products parsed for '{query}'. Generating mock products.")
            products = self.generate_fake_products(query, limit=limit, source="amazon")

        return products
