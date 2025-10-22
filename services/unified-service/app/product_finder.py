# app/product_finder.py — HTTP client to product-finder (8003)

import aiohttp
from typing import Dict, Any
from .models import Product, ProductSearchRequest, ProductSearchResponse, ProductDetailsResponse
from .config import PRODUCT_FINDER_URL


def _normalize_product_dict(p: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(p)
    # normalize fields that might vary between scrapers
    if "image" in q and "image_url" not in q:
        q["image_url"] = q["image"]
    try:
        q["price"] = float(str(q.get("price", 0)).replace("$", "").replace(",", ""))
    except Exception:
        q["price"] = 0.0
    if not q.get("source"):
        q["source"] = "unknown"
    return q


async def _post_json(path: str, payload: Dict[str, Any]):
    url = f"{PRODUCT_FINDER_URL}{path}"
    # Increase total timeout to 80s (was 40s)
    timeout = aiohttp.ClientTimeout(total=80)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                raise RuntimeError(f"POST {path} failed {resp.status}: {text}")
            if resp.status >= 400:
                raise RuntimeError(f"POST {path} failed {resp.status}: {data}")
            return data


async def _get_json(path: str, params: Dict[str, Any]):
    url = f"{PRODUCT_FINDER_URL}{path}"
    # Increase total timeout to 80s (was 40s)
    timeout = aiohttp.ClientTimeout(total=80)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                raise RuntimeError(f"GET {path} failed {resp.status}: {text}")
            if resp.status >= 400:
                raise RuntimeError(f"GET {path} failed {resp.status}: {data}")
            return data


# ---- Search -------------------------------------------------------------

async def search_products(request: ProductSearchRequest) -> ProductSearchResponse:
    payload = request.model_dump()
    payload.setdefault("sources", ["amazon", "ebay", "walmart"])
    payload.setdefault("fallback", True)

    data = await _post_json("/v1/products:search", payload)
    raw_products = data.get("products", [])
    products = [Product(**_normalize_product_dict(p)) for p in raw_products]

    return ProductSearchResponse(
        products=products,
        total_results=data.get("total_results", len(products)),
        query=data.get("query", payload.get("query", "")),
        filters_applied=data.get("filters_applied", {})
    )


# keep alias used elsewhere
search_products_unified = search_products


# ---- Details -------------------------------------------------------------

async def get_product_details(product_id: str, source: str = "amazon") -> ProductDetailsResponse:
    params = {"product_id": product_id, "source": source}
    data = await _get_json("/v1/products:details", params)
    product = Product(**_normalize_product_dict(data["product"]))
    return ProductDetailsResponse(product=product, additional_info=data.get("additional_info"))


# ---- Categories ------------------------------------------------------------

async def get_categories():
    data = await _get_json("/v1/products:categories", {})
    return data.get("categories", [])
