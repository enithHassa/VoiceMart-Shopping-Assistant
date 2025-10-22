# app/main.py (product-finder)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="VoiceMart Product Finder",
    version="1.0.0",
    description="Product search and discovery API for VoiceMart Shopping Assistant"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
from .models import (
    Product,
    ProductSearchRequest,
    ProductSearchResponse,
    ProductDetailsResponse,
)

SUPPORTED_SOURCES = {"amazon", "ebay", "walmart"}

# Root
@app.get("/")
async def root():
    return {
        "message": "VoiceMart Product Finder API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "search": "/v1/products:search",
            "details": "/v1/products:details",
            "categories": "/v1/products:categories"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# --- Search ------------------------------------------------------------------

@app.post("/v1/products:search", response_model=ProductSearchResponse)
async def search_products(request: ProductSearchRequest):
    """Search for products across Amazon, eBay, Walmart (scrapers)."""
    try:
        logger = logging.getLogger("api")
        logger.info(f"Received search request: {request.dict()}")
        from .api_clients import search_products_unified
        result = await search_products_unified(request)
        logger.info(f"Search returned {len(result.products)} products")
        return result
    except Exception as e:
        logger = logging.getLogger("api")
        logger.error(f"Product search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Product search failed: {str(e)}")

# Hide alias in Swagger to avoid duplicate listing
@app.post("/v1/products/search", response_model=ProductSearchResponse, include_in_schema=False)
async def search_products_alias(request: ProductSearchRequest):
    try:
        from .api_clients import search_products_unified
        return await search_products_unified(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product search failed: {str(e)}")

# --- Details (SCRAPER-ONLY, URL REQUIRED) ------------------------------------

@app.get("/v1/products:details")
async def get_product_details(
    product_id: str = Query(..., description="Full product URL (http/https), URL-encoded in query"),
    source: str = Query("amazon", description="One of: amazon, ebay, walmart")
):
    """
    Get detailed product info using scrapers.
    - product_id MUST be a full product URL (http/https)
    - source MUST be one of: amazon | ebay | walmart
    """
    try:
        if not (product_id.startswith("http://") or product_id.startswith("https://")):
            raise HTTPException(status_code=400, detail="product_id must be a full product URL (http/https).")
        if source not in SUPPORTED_SOURCES:
            raise HTTPException(status_code=422, detail=f"Unsupported source '{source}'. Allowed: {sorted(SUPPORTED_SOURCES)}")

        from .api_clients import get_product_details as get_details_impl
        result = await get_details_impl(product_id, source)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product details: {str(e)}")

# Hide alias in Swagger
@app.get("/v1/products/details", include_in_schema=False)
async def get_product_details_alias(product_id: str, source: str = "amazon"):
    return await get_product_details(product_id, source)

# --- Categories ---------------------------------------------------------------

@app.get("/v1/products:categories")
async def get_product_categories():
    """Get available product categories."""
    try:
        from .api_clients import get_categories
        categories = await get_categories()
        return {"categories": categories, "total": len(categories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/v1/products/categories", include_in_schema=False)
async def get_product_categories_alias():
    return await get_product_categories()
