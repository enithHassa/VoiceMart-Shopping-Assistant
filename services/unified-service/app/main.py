# app/main.py (unified-service)

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import logging
import json
import time
from dotenv import load_dotenv
from sqlalchemy.orm import Session

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
from .database import get_db, create_tables
from .services.conversation_manager import process_voice_query, get_conversation, clear_conversation
from .services.user_service import UserService
from .services.search_history_service import SearchHistoryService
from .services.recommendation_service import RecommendationService
from .services.advanced_recommendation_service import AdvancedRecommendationService

load_dotenv()
logger = logging.getLogger("unified-service")

# Initialize database tables
create_tables()

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

@app.post("/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}

@app.post("/test-search")
async def test_search_endpoint():
    """Simple test search that returns mock data immediately."""
    mock_products = [
        {
            "id": "test_1",
            "title": "Test Wireless Headphones",
            "price": 99.99,
            "currency": "USD",
            "image_url": "https://via.placeholder.com/300x300?text=Test+Product",
            "description": "This is a test product for debugging",
            "brand": "TestBrand",
            "category": "Electronics",
            "rating": 4.5,
            "availability": "In Stock",
            "url": "https://example.com/test",
            "source": "test"
        }
    ]
    
    return {
        "products": mock_products,
        "total_results": len(mock_products),
        "query": "test query",
        "filters_applied": {}
    }

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

@app.post("/v1/stt:transcribe")
async def transcribe_audio_endpoint(
    file: UploadFile = File(...),
    locale: Optional[str] = Form("en-US"),
):
    """Simple STT endpoint that just transcribes audio to text."""
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read file contents
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        logger.info(f"Transcribing audio: {file.filename}, size: {len(contents)} bytes")
        
        # Transcribe audio
        stt_result = transcribe_audio(contents, detect_language=True)
        transcript_text = stt_result.text or ""
        
        return {
            "text": transcript_text,
            "language": stt_result.language,
            "confidence": 0.9,  # Mock confidence
            "duration": stt_result.duration
        }
    except Exception as e:
        logger.exception("STT transcription error")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/v1/voice:shop")
async def voice_shop_simple(
    file: UploadFile = File(...),
    locale: Optional[str] = Form("en-US"),
):
    """Voice shop endpoint that processes audio and returns transcript + products."""
    try:
        # Validate audio
        content_type = file.content_type or ""
        if not is_allowed_mime(content_type):
            raise HTTPException(status_code=415, detail=f"Unsupported media type: {content_type}")

        contents = await file.read()
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024
        if len(contents) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File too large (> {MAX_UPLOAD_MB}MB)")

        # Transcribe audio
        stt_result = transcribe_audio(contents, detect_language=True)
        transcript_text = stt_result.text or ""

        # Process query
        qp_dict = process_query(transcript_text, None, locale)
        query_response = QueryResponse(**qp_dict)

        # Search for products if it's a search intent
        products = []
        product_search_performed = False
        if transcript_text and query_response.intent in {"search", "search_product"}:
            try:
                from .product_finder import search_products
                req = ProductSearchRequest(
                    query=transcript_text,
                    limit=8,
                    sources=["amazon", "ebay", "walmart"],
                    fallback=True,
                )
                search_result = await search_products(req)
                products = search_result.products or []
                product_search_performed = True
            except Exception as e:
                logger.warning(f"Product search failed, using mock data: {e}")
                # Return mock products when search fails
                products = [
                    {
                        "id": f"voice_mock_1",
                        "title": f"Voice Search Result for '{transcript_text}'",
                        "price": 79.99,
                        "currency": "USD",
                        "image_url": "https://via.placeholder.com/300x300?text=Voice+Search+Result",
                        "description": f"Product found via voice search for: {transcript_text}",
                        "brand": "VoiceMart",
                        "category": "Electronics",
                        "rating": 4.3,
                        "availability": "In Stock",
                        "url": "https://example.com/voice-product",
                        "source": "voice_search"
                    }
                ]
                product_search_performed = True

        return {
            "transcript": {
                "text": transcript_text,
                "language": stt_result.language or "en",
                "confidence": stt_result.confidence or 0.9,
                "duration": stt_result.duration or 1.0,
                "segments": stt_result.segments or []
            },
            "query": {
                "intent": query_response.intent,
                "confidence": query_response.confidence,
                "slots": query_response.slots,
                "reply": query_response.reply,
                "action": query_response.action,
                "user_id": None,
                "locale": locale
            },
            "products": products,
            "product_search_performed": product_search_performed
        }
    except Exception as e:
        logger.exception("Voice shop error")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ---------------------- Conversational Voice Shopping ----------------------

@app.post("/v1/voice:converse")
async def voice_converse(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    user_id: Optional[str] = Form(None),
    locale: Optional[str] = Form("en-US"),
    reset: bool = Form(False)
):
    """
    Conversational voice shopping - maintains context across multiple voice commands
    Returns follow-up questions or products based on conversation state
    """
    try:
        # Validate audio
        content_type = file.content_type or ""
        if not is_allowed_mime(content_type):
            raise HTTPException(status_code=415, detail=f"Unsupported media type: {content_type}")

        contents = await file.read()
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024
        if len(contents) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File too large (> {MAX_UPLOAD_MB}MB)")

        # Transcribe audio
        stt_result = transcribe_audio(contents, detect_language=True)
        transcript_text = stt_result.text or ""

        # Process with conversation manager
        conv_response = process_voice_query(session_id, user_id, transcript_text, reset)
        
        # If conversation is ready to search, perform product search
        products = []
        product_search_performed = False
        
        if conv_response.get("ready_to_search") and conv_response.get("search_params"):
            search_params = conv_response["search_params"]
            try:
                from .product_finder import search_products
                price_range = search_params.get("price_range") or {}
                req = ProductSearchRequest(
                    query=search_params.get("query", transcript_text),
                    category=search_params.get("category"),
                    min_price=price_range.get("min") if price_range else None,
                    max_price=price_range.get("max") if price_range else None,
                    brand=search_params.get("brand"),
                    limit=8,
                    sources=["amazon", "ebay", "walmart"],
                    fallback=True,
                )
                search_result = await search_products(req)
                products = search_result.products or []
                product_search_performed = True
            except Exception as e:
                logger.warning(f"Product search failed in conversation: {e}")
                product_search_performed = False

        return {
            "transcript": {
                "text": transcript_text,
                "language": stt_result.language or "en",
                "confidence": getattr(stt_result, 'confidence', None) or 0.9,
                "duration": stt_result.duration or 1.0,
            },
            "conversation": {
                "session_id": session_id,
                "query": conv_response.get("query", transcript_text),
                "question": conv_response.get("question"),  # Follow-up question or None
                "ready_to_search": conv_response.get("ready_to_search", False)
            },
            "products": products,
            "product_search_performed": product_search_performed
        }
    except Exception as e:
        logger.exception("Voice conversation error")
        raise HTTPException(status_code=500, detail=f"Conversation error: {str(e)}")

@app.post("/v1/voice:conversation/clear")
async def clear_conversation_endpoint(session_id: str = Form(...)):
    """Clear conversation state"""
    clear_conversation(session_id)
    return {"message": "Conversation cleared", "session_id": session_id}

@app.post("/v1/voice:conversation/test")
async def test_conversation(
    text: str = Form(...),
    session_id: str = Form(...),
    user_id: Optional[str] = Form(None),
    reset: bool = Form(False)
):
    """
    Test endpoint for conversation - accepts text directly (no audio)
    For testing purposes only
    """
    try:
        # Process with conversation manager
        conv_response = process_voice_query(session_id, user_id, text, reset)
        
        # If conversation is ready to search, perform product search
        products = []
        product_search_performed = False
        
        if conv_response.get("ready_to_search") and conv_response.get("search_params"):
            search_params = conv_response["search_params"]
            try:
                from .product_finder import search_products
                price_range = search_params.get("price_range") or {}
                req = ProductSearchRequest(
                    query=search_params.get("query", text),
                    category=search_params.get("category"),
                    min_price=price_range.get("min") if price_range else None,
                    max_price=price_range.get("max") if price_range else None,
                    brand=search_params.get("brand"),
                    limit=8,
                    sources=["amazon", "ebay", "walmart"],
                    fallback=True,
                )
                search_result = await search_products(req)
                products = search_result.products or []
                product_search_performed = True
            except Exception as e:
                logger.warning(f"Product search failed in conversation test: {e}")
                product_search_performed = False

        return {
            "transcript": {
                "text": text,
                "language": "en",
                "confidence": 1.0,
                "duration": 0.0,
            },
            "conversation": {
                "session_id": session_id,
                "query": conv_response.get("query", text),
                "question": conv_response.get("question"),
                "ready_to_search": conv_response.get("ready_to_search", False)
            },
            "products": products,
            "product_search_performed": product_search_performed
        }
    except Exception as e:
        logger.exception("Voice conversation test error")
        raise HTTPException(status_code=500, detail=f"Conversation test error: {str(e)}")

@app.post("/v1/voice:shop-old", response_model=VoiceUnderstandResponse)
async def voice_shop_old(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    locale: Optional[str] = Form("en-US"),
):
    # Debug logging
    logger.info(f"Voice shop request - filename: {file.filename}, content_type: {file.content_type}, size: {file.size}")
    
    # Validate audio
    content_type = file.content_type or ""
    logger.info(f"Checking MIME type: '{content_type}'")
    
    if not is_allowed_mime(content_type):
        logger.warning(f"Unsupported media type: {content_type}")
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

@app.post("/search")
async def search_products_simple(request: ProductSearchRequest):
    """Simple search endpoint for frontend compatibility."""
    try:
        from .product_finder import search_products
        result = await search_products(request)
        return result
    except Exception as e:
        logger.warning(f"Product search failed, returning mock data: {str(e)}")
        # Return mock data when product-finder fails
        mock_products = [
            {
                "id": "mock_1",
                "title": f"Mock Product for '{request.query}'",
                "price": 99.99,
                "currency": "USD",
                "image_url": "https://via.placeholder.com/300x300?text=Product+Image",
                "description": f"This is a mock product for the search query: {request.query}",
                "brand": "MockBrand",
                "category": "Electronics",
                "rating": 4.5,
                "availability": "In Stock",
                "url": "https://example.com/product",
                "source": "mock"
            },
            {
                "id": "mock_2", 
                "title": f"Another Mock Product for '{request.query}'",
                "price": 149.99,
                "currency": "USD",
                "image_url": "https://via.placeholder.com/300x300?text=Product+2",
                "description": f"Another mock product for: {request.query}",
                "brand": "MockBrand",
                "category": "Electronics",
                "rating": 4.2,
                "availability": "In Stock",
                "url": "https://example.com/product2",
                "source": "mock"
            }
        ]
        
        return {
            "products": mock_products,
            "total_results": len(mock_products),
            "query": request.query,
            "filters_applied": {}
        }

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


# ---- Search History Endpoints ----

@app.post("/v1/search-history")
async def save_search_history_endpoint(
    user_id: str = Form(...),
    query: str = Form(...),
    sources: str = Form(...),  # JSON string
    result_count: int = Form(...),
    db: Session = Depends(get_db)
):
    """Save a search to user's history"""
    try:
        sources_list = json.loads(sources)
        search_service = SearchHistoryService(db)
        history_item = search_service.save_search_history(user_id, query, sources_list, result_count)
        return {"success": True, "item": history_item.to_dict()}
    except Exception as e:
        logger.exception("Failed to save search history")
        raise HTTPException(status_code=500, detail=f"Failed to save search history: {str(e)}")

@app.get("/v1/search-history/{user_id}")
async def get_search_history_endpoint(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get search history for a user"""
    try:
        search_service = SearchHistoryService(db)
        history = search_service.get_search_history(user_id, limit)
        return {"history": history, "total": len(history)}
    except Exception as e:
        logger.exception("Failed to get search history")
        raise HTTPException(status_code=500, detail=f"Failed to get search history: {str(e)}")

@app.delete("/v1/search-history/{user_id}")
async def clear_search_history_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Clear all search history for a user"""
    try:
        search_service = SearchHistoryService(db)
        success = search_service.clear_search_history(user_id)
        return {"success": success}
    except Exception as e:
        logger.exception("Failed to clear search history")
        raise HTTPException(status_code=500, detail=f"Failed to clear search history: {str(e)}")

@app.delete("/v1/search-history/{user_id}/{item_id}")
async def delete_search_history_item_endpoint(user_id: str, item_id: str, db: Session = Depends(get_db)):
    """Delete a specific search history item"""
    try:
        search_service = SearchHistoryService(db)
        success = search_service.delete_search_history_item(user_id, item_id)
        return {"success": success}
    except Exception as e:
        logger.exception("Failed to delete search history item")
        raise HTTPException(status_code=500, detail=f"Failed to delete search history item: {str(e)}")

@app.get("/v1/search-analytics/{user_id}")
async def get_search_analytics_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Get search analytics for a user"""
    try:
        search_service = SearchHistoryService(db)
        analytics = search_service.get_search_analytics(user_id)
        return analytics
    except Exception as e:
        logger.exception("Failed to get search analytics")
        raise HTTPException(status_code=500, detail=f"Failed to get search analytics: {str(e)}")


# ---- Recommendation Endpoints ----

@app.get("/v1/recommendations/search-suggestions/{user_id}")
async def get_search_suggestions_endpoint(
    user_id: str, 
    current_query: str = "", 
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get search suggestions for a user"""
    try:
        rec_service = RecommendationService(db)
        suggestions = rec_service.generate_search_suggestions(user_id, current_query, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.exception("Failed to get search suggestions")
        raise HTTPException(status_code=500, detail=f"Failed to get search suggestions: {str(e)}")

@app.get("/v1/recommendations/products/{user_id}")
async def get_product_recommendations_endpoint(
    user_id: str,
    current_query: str = "",
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get comprehensive product recommendations for a user"""
    try:
        advanced_rec_service = AdvancedRecommendationService(db)
        recommendations = advanced_rec_service.generate_comprehensive_recommendations(user_id, limit)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.exception("Failed to get product recommendations")
        raise HTTPException(status_code=500, detail=f"Failed to get product recommendations: {str(e)}")

@app.post("/v1/track-interaction")
async def track_product_interaction_endpoint(
    user_id: str = Form(...),
    product_id: str = Form(...),
    product_title: str = Form(...),
    product_category: Optional[str] = Form(None),
    product_brand: Optional[str] = Form(None),
    product_price: Optional[float] = Form(None),
    source: str = Form(...),
    interaction_type: str = Form(...),
    search_query: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Track user interaction with a product"""
    try:
        rec_service = RecommendationService(db)
        interaction = rec_service.track_product_interaction(
            user_id=user_id,
            product_id=product_id,
            product_title=product_title,
            product_category=product_category,
            product_brand=product_brand,
            product_price=product_price,
            source=source,
            interaction_type=interaction_type,
            search_query=search_query,
            session_id=session_id
        )
        return {"success": True, "interaction_id": str(interaction.id)}
    except Exception as e:
        logger.exception("Failed to track product interaction")
        raise HTTPException(status_code=500, detail=f"Failed to track interaction: {str(e)}")


# ---- User Authentication Endpoints ----

@app.post("/v1/auth/register")
async def register_user(
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    phone: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user_service = UserService(db)
        user = user_service.create_user(email, name, password, phone)
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "message": "User registered successfully"
        }
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail="Email already registered. Please use a different email or try logging in.")
        else:
            raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")
    except Exception as e:
        logger.exception("Failed to register user")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/v1/auth/login")
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login user"""
    try:
        user_service = UserService(db)
        user = user_service.authenticate_user(email, password)
        if user:
            # Generate a simple token (in production, use JWT)
            token = f"token_{user.id}_{int(time.time())}"
            return {
                "success": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                "token": token,
                "message": "Login successful"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.exception("Failed to login user")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.get("/v1/auth/profile/{user_id}")
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Get user profile"""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if user:
            return {
                "success": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.exception("Failed to get user profile")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@app.put("/v1/auth/profile/{user_id}")
async def update_user_profile(
    user_id: str,
    name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    try:
        user_service = UserService(db)
        user = user_service.update_user_profile(user_id, name, phone)
        if user:
            return {
                "success": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                "message": "Profile updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.exception("Failed to update user profile")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@app.get("/v1/auth/users")
async def list_users(db: Session = Depends(get_db)):
    """List all users (for debugging)"""
    try:
        user_service = UserService(db)
        users = user_service.get_all_users()
        return {
            "success": True,
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ],
            "total": len(users)
        }
    except Exception as e:
        logger.exception("Failed to list users")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")
