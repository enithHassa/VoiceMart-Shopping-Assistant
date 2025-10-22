# app/api_clients.py - Product API integrations (scraper-first)
import asyncio
import aiohttp
import re
from typing import List, Dict, Any
from .models import Product, ProductSearchRequest, ProductSearchResponse, ProductDetailsResponse
import os
import logging
from dotenv import load_dotenv
from .scrapers import AmazonScraper, EbayScraper, WalmartScraper, ScraperManager

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scrapers
amazon_scraper = AmazonScraper()
ebay_scraper = EbayScraper()
walmart_scraper = WalmartScraper()
scraper_manager = ScraperManager([amazon_scraper, ebay_scraper, walmart_scraper])


# ---- Search -------------------------------------------------------------

async def search_products_unified(request: ProductSearchRequest) -> ProductSearchResponse:
    sources = [s.lower() for s in (request.sources or ["amazon", "ebay", "walmart"])]
    logger.info(f"Searching for '{request.query}' across: {sources}")

    loop = asyncio.get_event_loop()
    scraper_results = await loop.run_in_executor(
        None,
        lambda: scraper_manager.search_products(
            query=request.query,
            limit=request.limit * 2,
            sources=sources,
            parallel=True
        )
    )

    if not scraper_results and getattr(request, "fallback", True):
        fallback_sources = ['amazon', 'ebay', 'walmart']
        logger.info(f"Fallback triggered to all sources: {fallback_sources}")
        scraper_results = await loop.run_in_executor(
            None,
            lambda: scraper_manager.search_products(
                query=request.query,
                limit=request.limit * 2,
                sources=fallback_sources,
                parallel=True
            )
        )

    logger.info(f"Got {len(scraper_results)} raw results")

    # Filter + normalize
    products: List[Product] = []
    for item in scraper_results:
        try:
            price = float(str(item.get('price', 0)).replace('$', '').replace(',', ''))
        except Exception:
            price = 0.0
        item['price'] = price

        if request.min_price and price < request.min_price:
            continue
        if request.max_price and price > request.max_price:
            continue

        if request.brand:
            brand = request.brand.lower()
            title = (item.get('title') or '').lower()
            if brand not in title:
                continue

        products.append(Product(
            id=item.get('id', str(hash(item.get('url', '') + item.get('title', '')))),
            title=item.get('title', 'Unknown'),
            price=price,
            currency="USD",
            image_url=item.get('image_url') or item.get('image'),
            description=item.get('description', ''),
            category=item.get('category', ''),
            brand=item.get('brand'),
            rating=item.get('rating'),
            availability="in_stock",
            url=item.get('url', ''),
            source=item.get('source', 'unknown'),
        ))

    products.sort(key=lambda x: (request.query.lower() in x.title.lower(), x.rating or 0), reverse=True)
    limited = products[:request.limit]

    return ProductSearchResponse(
        products=limited,
        total_results=len(limited),
        query=request.query,
        filters_applied={
            "category": request.category,
            "min_price": request.min_price,
            "max_price": request.max_price,
            "brand": request.brand,
            "sources": sources
        }
    )


# ---- Details -------------------------------------------------------------

async def get_product_details(product_id: str, source: str = "amazon") -> ProductDetailsResponse:
    if not product_id.startswith(("http://", "https://")):
        raise Exception("product_id must be a full product URL.")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: scraper_manager.get_product_details(product_id, source)
    )

    if not result:
        raise Exception(f"Product not found or unsupported URL for '{source}'.")

    price = result.get('price', 0)
    try:
        price = float(str(price).replace('$', '').replace(',', ''))
    except Exception:
        price = 0.0

    product = Product(
        id=str(hash(result.get('url', '') or product_id)),
        title=result.get('title', 'Unknown'),
        price=price,
        currency="USD",
        image_url=result.get('image') or result.get('image_url'),
        description=result.get('description', ''),
        category=result.get('category', ''),
        rating=None,
        availability="in_stock",
        url=result.get('url', '') or product_id,
        source=source
    )

    return ProductDetailsResponse(
        product=product,
        additional_info={
            "source": source,
            "fetched_at": "2025-10-17T00:00:00Z",
            "details": result.get('details', {})
        }
    )


# ---- Categories -------------------------------------------------------------

async def get_categories() -> List[Dict[str, Any]]:
    return [
        {"id": "electronics", "name": "Electronics", "source": "all"},
        {"id": "smartphones", "name": "Smartphones", "source": "all"},
        {"id": "laptops", "name": "Laptops", "source": "all"},
        {"id": "tablets", "name": "Tablets", "source": "all"},
        {"id": "headphones", "name": "Headphones", "source": "all"},
        {"id": "wearables", "name": "Wearables", "source": "all"},
        {"id": "smart_home", "name": "Smart Home", "source": "all"},
        {"id": "cameras", "name": "Cameras", "source": "all"},
        {"id": "gaming", "name": "Gaming", "source": "all"},
        {"id": "audio", "name": "Audio", "source": "all"},
        {"id": "tv", "name": "TVs", "source": "all"},
        {"id": "computers", "name": "Computers", "source": "all"},
        {"id": "appliances", "name": "Appliances", "source": "all"},
        {"id": "collectibles", "name": "Collectibles", "source": "ebay"},
        {"id": "motors", "name": "Motors", "source": "ebay"},
        {"id": "grocery", "name": "Grocery", "source": "walmart"},
        {"id": "pharmacy", "name": "Pharmacy", "source": "walmart"},
        {"id": "baby", "name": "Baby", "source": "walmart"},
    ]
