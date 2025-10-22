from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger('ebay_scraper')

class EbayScraper(BaseScraper):
    def __init__(self, **kwargs):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
        ]
        super().__init__(use_selenium=False, **kwargs)
        self.base_url = "https://www.ebay.com"

    def search_products(self, query, limit=5):
        """Search for products on eBay"""
        # ask for more items per page to reduce paging/latency flakiness
        search_url = f"{self.base_url}/sch/i.html?_nkw={query.replace(' ', '+')}&_ipg=60"
        logger.info(f"Searching eBay for: {query}")

        html = self.get_page_content(search_url)
        if not html:
            logger.warning(f"Failed to get content from eBay for query: {query}")
            return self.generate_fake_products(query, limit=limit, source="ebay")

        soup = self.parse_html(html)
        if not soup:
            return self.generate_fake_products(query, limit=limit, source="ebay")

        products = []

        result_selectors = [
            ".srp-results .s-item",
            ".srp-list .s-item",
            "li.s-item",
        ]

        results = []
        for selector in result_selectors:
            results = soup.select(selector)
            if results:
                # drop “More items like this” placeholders
                results = [r for r in results if not r.select_one('.srp-save--more-like')]
                if results:
                    logger.info(f"Found {len(results)} eBay results using selector: {selector}")
                    break

        for item in results[:limit]:
            product = {"source": "ebay", "category": query}

            # Title
            for sel in [".s-item__title", ".s-item__title span", "h3.s-item__title", ".s-item__info a h3"]:
                el = item.select_one(sel)
                if el and el.text.strip() and 'Shop on eBay' not in el.text:
                    product['title'] = el.text.strip().replace('New Listing', '').strip()
                    break

            # Price (handle ranges)
            for sel in [".s-item__price", "span.s-item__price", ".s-item__detail--primary .s-item__price"]:
                el = item.select_one(sel)
                if el:
                    txt = el.text.strip()
                    if ' to ' in txt:
                        txt = txt.split(' to ')[0]
                    m = re.search(r'(\$[\d,]+\.\d+)|(\$[\d,]+)', txt)
                    if m:
                        product['price'] = float(m.group(0).replace('$', '').replace(',', ''))
                        break

            # Image (data-src or src)
            for sel in [".s-item__image-img", ".s-item__image img"]:
                img = item.select_one(sel)
                if img:
                    url = img.get('data-src') or img.get('src')
                    if url and 'ir.ebaystatic.com' not in url:
                        product['image'] = url
                        break

            # URL (strip tracking params)
            for sel in [".s-item__link", ".s-item__info a"]:
                a = item.select_one(sel)
                if a and a.get('href'):
                    href = a['href']
                    if '?' in href:
                        href = href.split('?')[0]
                    product['url'] = href
                    break

            # Simple description
            if 'title' in product:
                product['description'] = product['title']
                products.append(product)

        if not products and query:
            logger.warning(f"No eBay products parsed for '{query}'. Generating mock products.")
            products = self.generate_fake_products(query, limit=limit, source="ebay")

        return products
