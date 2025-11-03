# eBay API Client
import aiohttp
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('ebay_api')

class EbayAPIClient:
    def __init__(self, client_id: Optional[str] = None):
        self.client_id = client_id or ""  # Replace with actual client ID
        self.base_url = "https://api.ebay.com"
        self.headers = {
            "Authorization": f"Bearer {self.client_id}",
            "Content-Type": "application/json"
        }
    
    async def search_products(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for products using eBay Browse API"""
        if not self.client_id or self.client_id == "YOUR_EBAY_CLIENT_ID":
            logger.warning("eBay API not configured, returning mock data")
            return self._generate_mock_products(query, limit)
        
        try:
            url = f"{self.base_url}/buy/browse/v1/item_summary/search"
            params = {
                "q": query,
                "limit": min(limit, 200),  # eBay max is 200
                "sort": "price",
                "filter": "conditionIds:{3000|4000|5000}"  # New, Used, Refurbished
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_ebay_response(data, query)
                    else:
                        logger.error(f"eBay API error: {response.status}")
                        return self._generate_mock_products(query, limit)
        except Exception as e:
            logger.error(f"eBay API request failed: {e}")
            return self._generate_mock_products(query, limit)
    
    def _parse_ebay_response(self, data: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Parse eBay API response into our product format"""
        products = []
        
        for item in data.get("itemSummaries", []):
            try:
                # Extract price
                price = 0.0
                if "price" in item:
                    price_info = item["price"]
                    if "value" in price_info:
                        price = float(price_info["value"])
                
                # Extract image
                image_url = None
                if "image" in item and "imageUrl" in item["image"]:
                    image_url = item["image"]["imageUrl"]
                
                product = {
                    "id": item.get("itemId", ""),
                    "title": item.get("title", ""),
                    "price": price,
                    "currency": "USD",
                    "image_url": image_url,
                    "description": item.get("title", ""),
                    "brand": None,
                    "category": query,
                    "rating": None,
                    "availability": "in_stock",
                    "url": item.get("itemWebUrl", ""),
                    "source": "ebay"
                }
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse eBay item: {e}")
                continue
        
        return products
    
    def _generate_mock_products(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Generate mock eBay products when API is not available"""
        mock_products = []
        for i in range(limit):
            product = {
                "id": f"ebay_mock_{i+1}",
                "title": f"eBay {query.title()} - Item {i+1}",
                "price": round(50 + (i * 25) + (hash(query) % 100), 2),
                "currency": "USD",
                "image_url": f"https://via.placeholder.com/300x300?text=eBay+{query}",
                "description": f"eBay listing for {query}",
                "brand": "eBay Seller",
                "category": query,
                "rating": round(4.0 + (i * 0.1), 1),
                "availability": "in_stock",
                "url": f"https://www.ebay.com/itm/mock-{i+1}",
                "source": "ebay"
            }
            mock_products.append(product)
        return mock_products
