# Walmart API Client
import aiohttp
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('walmart_api')

class WalmartAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "YOUR_WALMART_API_KEY"  # Replace with actual API key
        self.base_url = "https://marketplace.walmartapis.com"
        self.headers = {
            "WM_QOS.CORRELATION_ID": "test",
            "WM_SVC.NAME": "Walmart Marketplace",
            "Content-Type": "application/json"
        }
        if self.api_key != "YOUR_WALMART_API_KEY":
            self.headers["Authorization"] = f"Basic {self.api_key}"
    
    async def search_products(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for products using Walmart Catalog API"""
        if not self.api_key or self.api_key == "YOUR_WALMART_API_KEY":
            logger.warning("Walmart API not configured, returning mock data")
            return self._generate_mock_products(query, limit)
        
        try:
            url = f"{self.base_url}/v3/items/walmart/search"
            params = {
                "query": query,
                "numItems": min(limit, 25),  # Walmart max is 25
                "format": "json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_walmart_response(data, query)
                    else:
                        logger.error(f"Walmart API error: {response.status}")
                        return self._generate_mock_products(query, limit)
        except Exception as e:
            logger.error(f"Walmart API request failed: {e}")
            return self._generate_mock_products(query, limit)
    
    def _parse_walmart_response(self, data: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Parse Walmart API response into our product format"""
        products = []
        
        for item in data.get("items", []):
            try:
                # Extract price
                price = 0.0
                if "salePrice" in item:
                    price = float(item["salePrice"])
                elif "price" in item:
                    price = float(item["price"])
                
                # Extract image
                image_url = None
                if "imageEntities" in item and item["imageEntities"]:
                    image_url = item["imageEntities"][0].get("largeImageUrl")
                
                product = {
                    "id": item.get("itemId", ""),
                    "title": item.get("name", ""),
                    "price": price,
                    "currency": "USD",
                    "image_url": image_url,
                    "description": item.get("shortDescription", ""),
                    "brand": item.get("brandName"),
                    "category": query,
                    "rating": item.get("averageRating"),
                    "availability": "in_stock" if item.get("available") else "out_of_stock",
                    "url": item.get("productUrl", ""),
                    "source": "walmart"
                }
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse Walmart item: {e}")
                continue
        
        return products
    
    def _generate_mock_products(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Generate mock Walmart products when API is not available"""
        mock_products = []
        for i in range(limit):
            product = {
                "id": f"walmart_mock_{i+1}",
                "title": f"Walmart {query.title()} - Product {i+1}",
                "price": round(30 + (i * 20) + (hash(query) % 50), 2),
                "currency": "USD",
                "image_url": f"https://via.placeholder.com/300x300?text=Walmart+{query}",
                "description": f"Walmart product for {query}",
                "brand": "Walmart",
                "category": query,
                "rating": round(4.2 + (i * 0.05), 1),
                "availability": "in_stock",
                "url": f"https://www.walmart.com/ip/mock-{i+1}",
                "source": "walmart"
            }
            mock_products.append(product)
        return mock_products
