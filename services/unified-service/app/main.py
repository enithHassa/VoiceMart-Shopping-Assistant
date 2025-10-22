# app/main.py (unified-service)

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import logging
from dotenv import load_dotenv

# Local imports
from .stt_engine import transcribe_audio, is_allowed_mime
from .config import MAX_UPLOAD_MB
from .models import (
    TranscriptionResult,
    QueryRequest, QueryResponse,
    Product, ProductSearchRequest, ProductSearchResponse, ProductDetailsResponse,
    VoiceUnderstandResponse
)
from .processor import process_query  # LLM agent lives here

load_dotenv()
logger = logging.getLogger("unified-service")

app = FastAPI(
    title="VoiceMart Unified Service",
    version="1.0.0",
    description="Unified API combining Speech-to-Text, Query Processing, and Product Finder proxy"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "VoiceMart Unified Service API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "stt": "/v1/stt:transcribe",
            "query": "/v1/query:process",
            "voice_understand": "/v1/voice:understand",     # STT + Query (no products)
            "voice_shop": "/v1/voice:shop",                 # STT + Query + Products
            "product_search": "/v1/products:search",
            "product_details": "/v1/products:details",
            "product_categories": "/v1/products:categories",
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# ---------------------- STT ----------------------

@app.post("/v1/stt:transcribe", response_model=TranscriptionResult)
async def stt_transcribe(file: UploadFile = File(...)):
    content_type = file.content_type or ""
    if not is_allowed_mime(content_type):
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {content_type}")

    contents = await file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (> {MAX_UPLOAD_MB}MB)")

    try:
        result = transcribe_audio(contents, detect_language=True)
        return JSONResponse(content=result.model_dump())
    except Exception as e:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=400, detail=f"Transcription failed: {str(e)}")

# ---------------------- Query agent (LLM) ----------------------

@app.post("/v1/query:process", response_model=QueryResponse)
async def query_process(req: QueryRequest):
    result = process_query(req.text, user_id=req.user_id, locale=req.locale)
    return result

# ---------------------- Voice = STT + Query (no products) ----------------------

@app.post("/v1/voice:understand", response_model=VoiceUnderstandResponse)
async def voice_understand(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    locale: Optional[str] = Form("en-US"),
):
    # Validate audio
    content_type = file.content_type or ""
    if not is_allowed_mime(content_type):
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {content_type}")

    contents = await file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (> {MAX_UPLOAD_MB}MB)")

    # Transcribe
    stt_result = transcribe_audio(contents, detect_language=True)
    transcript_text = stt_result.text or ""

    # Query process
    qp_dict = process_query(transcript_text, user_id, locale)
    query_response = QueryResponse(**qp_dict)

    # Return WITHOUT products
    return VoiceUnderstandResponse(
        transcript=stt_result,
        query=query_response,
        products=None,
        product_search_performed=False
    )

# ---------------------- NEW: Voice shopping (STT + Query + Products) ---------

@app.post("/v1/voice:shop", response_model=VoiceUnderstandResponse)
async def voice_shop(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    locale: Optional[str] = Form("en-US"),
):
    # Validate audio
    content_type = file.content_type or ""
    if not is_allowed_mime(content_type):
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {content_type}")

    contents = await file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (> {MAX_UPLOAD_MB}MB)")

    # 1) STT
    stt_result = transcribe_audio(contents, detect_language=True)
    transcript_text = (stt_result.text or "").strip()

    # 2) Query processing (intent + slots)
    qp_dict = process_query(transcript_text, user_id, locale)
    query_response = QueryResponse(**qp_dict)
    slots = qp_dict.get("slots", {}) or {}

    # 3) Build a CLEAN product-search query
    # Prefer "brand + product" (e.g., "nike shoes"); otherwise product; otherwise fallback to transcript.
    brand = (slots.get("brand") or "").strip()
    product = (slots.get("product") or "").strip()

    # If LLM wrote "Nike shoes" into product, avoid duplicating brand twice:
    if brand and product.lower().startswith(brand.lower()):
        clean_query = product
    else:
        clean_query = " ".join(x for x in [brand, product] if x).strip()

    if not clean_query:
        # last resort: use transcript but strip obvious price phrases like "under $100"
        import re
        price_phrase_re = re.compile(
            r"\b(?:under|below|less\s*than|over|above|more\s*than|at\s*least|between|from)\b.*$",
            re.I,
        )
        clean_query = price_phrase_re.sub("", transcript_text).strip()

    # 4) If intent is product-related, call product-finder(8003)
    products = None
    product_search_performed = False
    if query_response.intent in {"search_product", "add_to_cart"} and clean_query:
        try:
            from .product_finder import search_products  # HTTP client to 8003

            req = ProductSearchRequest(
                query=clean_query,                             # << use the cleaned query
                category=slots.get("category"),
                min_price=slots.get("price_min"),
                max_price=slots.get("price_max"),
                brand=brand or None,
                limit=8,
                sources=["amazon", "ebay", "walmart"],
                fallback=True,
            )
            search_result = await search_products(req)
            products = search_result.products or []
            product_search_performed = True

        except Exception:
            logger.exception("Product search failed during voice_shop")

    return VoiceUnderstandResponse(
        transcript=stt_result,
        query=query_response,
        products=products,
        product_search_performed=product_search_performed,
    )

# ---------------------- Product proxy -> product-finder(8003) ----------------

@app.post("/v1/products:search", response_model=ProductSearchResponse)
async def search_products_endpoint(request: ProductSearchRequest):
    try:
        from .product_finder import search_products  # HTTP client to 8003
        result = await search_products(request)
        return result
    except Exception as e:
        logger.exception("Product search failed")
        raise HTTPException(status_code=500, detail=f"Product search failed: {str(e)}")

# Put DETAILS before CATEGORIES so Swagger shows that order

@app.get("/v1/products:details")
async def get_product_details_endpoint(product_id: str, source: str = "amazon"):
    try:
        from .product_finder import get_product_details  # HTTP client to 8003
        result = await get_product_details(product_id, source)
        return result
    except Exception as e:
        logger.exception("Product details failed")
        raise HTTPException(status_code=500, detail=f"Failed to get product details: {str(e)}")

@app.get("/v1/products:categories")
async def get_product_categories_endpoint():
    try:
        from .product_finder import get_categories  # HTTP client to 8003
        categories = await get_categories()
        return {"categories": categories, "total": len(categories)}
    except Exception as e:
        logger.exception("Fetching categories failed")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")
