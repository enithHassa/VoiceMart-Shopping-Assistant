# Hybrid search that tries APIs first, then falls back to scraping
import asyncio
import logging
from typing import List, Dict, Any
from .scrapers import AmazonScraper, EbayScraper, WalmartScraper
from .api_clients.ebay_api import EbayAPIClient
from .api_clients.walmart_api import WalmartAPIClient

logger = logging.getLogger('hybrid_search')

class HybridProductSearch:
    def __init__(self):
        # Initialize scrapers
        self.amazon_scraper = AmazonScraper()
        self.ebay_scraper = EbayScraper()
        self.walmart_scraper = WalmartScraper()
        
        # Initialize API clients
        self.ebay_api = EbayAPIClient()
        self.walmart_api = WalmartAPIClient()
    
    async def search_products(self, query: str, sources: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Search products using hybrid approach: APIs first, then scraping"""
        all_products = []
        
        # Search each source sequentially to avoid conflicts
        for source in sources:
            try:
                logger.info(f"Searching {source} for: {query}")
                if source.lower() == "amazon":
                    # Amazon - use scraper (works well)
                    products = await self._search_amazon(query, limit)
                    all_products.extend(products)
                    logger.info(f"Amazon added {len(products)} products, total: {len(all_products)}")
                
                elif source.lower() == "ebay":
                    # eBay - try API first, then scraper
                    products = await self._search_ebay(query, limit)
                    all_products.extend(products)
                    logger.info(f"eBay added {len(products)} products, total: {len(all_products)}")
                
                elif source.lower() == "walmart":
                    # Walmart - try API first, then scraper
                    products = await self._search_walmart(query, limit)
                    all_products.extend(products)
                    logger.info(f"Walmart added {len(products)} products, total: {len(all_products)}")
                    
            except Exception as e:
                logger.error(f"Error searching {source}: {e}")
                import traceback
                logger.error(f"Traceback for {source}: {traceback.format_exc()}")
                continue
        
        logger.info(f"Final result: {len(all_products)} products from {sources}")
        return all_products[:limit * len(sources)]  # Limit total results
    
    async def _search_amazon(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Amazon using scraper"""
        try:
            logger.info(f"Starting Amazon search for: {query}")
            loop = asyncio.get_event_loop()
            products = await loop.run_in_executor(
                None, 
                lambda: self.amazon_scraper.search_products(query, limit)
            )
            logger.info(f"Amazon search returned {len(products)} products")
            return self._normalize_products(products, "amazon")
        except Exception as e:
            logger.error(f"Amazon search failed: {e}")
            import traceback
            logger.error(f"Amazon search traceback: {traceback.format_exc()}")
            return []
    
    async def _search_ebay(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search eBay using API first, then scraper"""
        try:
            # Try API first
            products = await self.ebay_api.search_products(query, limit)
            if products and not any("mock" in p.get("id", "") for p in products):
                logger.info(f"eBay API returned {len(products)} products")
                return products
            
            # Fall back to scraper
            logger.info("eBay API failed, trying scraper...")
            loop = asyncio.get_event_loop()
            products = await loop.run_in_executor(
                None,
                lambda: self.ebay_scraper.search_products(query, limit)
            )
            return self._normalize_products(products, "ebay")
        except Exception as e:
            logger.error(f"eBay search failed: {e}")
            return []
    
    async def _search_walmart(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Walmart using API first, then scraper"""
        try:
            # Try API first
            products = await self.walmart_api.search_products(query, limit)
            if products and not any("mock" in p.get("id", "") for p in products):
                logger.info(f"Walmart API returned {len(products)} products")
                return products
            
            # Fall back to scraper
            logger.info("Walmart API failed, trying scraper...")
            loop = asyncio.get_event_loop()
            products = await loop.run_in_executor(
                None,
                lambda: self.walmart_scraper.search_products(query, limit)
            )
            return self._normalize_products(products, "walmart")
        except Exception as e:
            logger.error(f"Walmart search failed: {e}")
            return []
    
    def _normalize_products(self, products: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
        """Normalize product data to consistent format"""
        normalized = []
        for product in products:
            try:
                # Ensure required fields
                normalized_product = {
                    "id": product.get("id", ""),
                    "title": product.get("title", "Unknown Product"),
                    "price": float(product.get("price", 0)),
                    "currency": product.get("currency", "USD"),
                    "image_url": product.get("image_url") or product.get("image"),
                    "description": product.get("description", ""),
                    "brand": product.get("brand"),
                    "category": product.get("category", ""),
                    "rating": product.get("rating"),
                    "availability": product.get("availability", "in_stock"),
                    "url": product.get("url", ""),
                    "source": source
                }
                normalized.append(normalized_product)
            except Exception as e:
                logger.warning(f"Failed to normalize product: {e}")
                continue
        return normalized
