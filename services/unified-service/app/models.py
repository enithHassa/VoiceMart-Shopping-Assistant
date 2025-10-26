# app/models.py - SQLAlchemy database models + Pydantic API models

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from .database import Base

# ===== PYDANTIC MODELS (for API) =====

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str

class TranscriptionResult(BaseModel):
    text: str = Field(..., description="Full transcription")
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[List[TranscriptionSegment]] = None

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    locale: str = "en-US"

class QueryResponse(BaseModel):
    intent: str
    confidence: float
    slots: Dict[str, Any]
    reply: str
    action: Dict[str, Any]
    user_id: Optional[str] = None
    locale: str = "en-US"

class Product(BaseModel):
    id: str
    title: str
    price: float
    currency: str = "USD"
    image_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = None
    availability: Optional[str] = None
    url: Optional[str] = None
    source: str

class ProductSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    brand: Optional[str] = None
    limit: int = 10
    sources: Optional[List[str]] = None
    fallback: bool = True

class ProductSearchResponse(BaseModel):
    products: List[Product]
    total_results: int
    query: str
    filters_applied: Dict[str, Any]

class ProductDetailsResponse(BaseModel):
    product: Product
    related_products: List[Product]

class VoiceUnderstandResponse(BaseModel):
    transcript: str
    intent: str
    confidence: float
    slots: Dict[str, Any]
    reply: str
    action: Dict[str, Any]
    products: Optional[List[Product]] = None
    user_id: Optional[str] = None
    locale: str = "en-US"

# ===== SQLALCHEMY MODELS (for database) =====

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255))  # Never store plain passwords
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    preferences = Column(JSON, default=dict)  # User preferences for recommendations
    
    # Relationships
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    product_interactions = relationship("ProductInteraction", back_populates="user", cascade="all, delete-orphan")
    user_preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    sources = Column(ARRAY(String), nullable=False)  # Array of sources: ['amazon', 'ebay', 'walmart']
    result_count = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(String(255))  # Track user sessions
    user_agent = Column(Text)  # Browser info for context
    ip_address = Column(String(45))  # IPv4/IPv6 address
    
    # Relationships
    user = relationship("User", back_populates="search_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_search_history_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_search_history_query', 'query'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "query": self.query,
            "sources": self.sources,
            "result_count": self.result_count,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "session_id": self.session_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address
        }

class ProductInteraction(Base):
    __tablename__ = "product_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(255), nullable=False)
    product_title = Column(Text, nullable=False)
    product_category = Column(String(255))
    product_brand = Column(String(255))
    product_price = Column(Float)
    source = Column(String(50), nullable=False)  # 'amazon', 'ebay', 'walmart'
    interaction_type = Column(String(50), nullable=False)  # 'view', 'click', 'search', 'purchase'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(String(255))
    search_query = Column(Text)  # The query that led to this interaction
    
    # Relationships
    user = relationship("User", back_populates="product_interactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_interactions_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_product_interactions_type', 'interaction_type'),
        Index('idx_product_interactions_source', 'source'),
    )

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(255), nullable=False)
    preference_value = Column(Float, default=0.5)  # 0.0 to 1.0 preference score
    confidence = Column(Float, default=0.1)  # How confident we are in this preference
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_preferences")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_user_preferences_user_category', 'user_id', 'category', unique=True),
    )

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recommendation_type = Column(String(50), nullable=False)  # 'search_suggestions', 'product_recommendations'
    recommendations = Column(JSON, nullable=False)  # The actual recommendations
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    model_version = Column(String(50), default='v1.0')
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    
    # Indexes
    __table_args__ = (
        Index('idx_recommendations_user_type', 'user_id', 'recommendation_type'),
        Index('idx_recommendations_expires', 'expires_at'),
    )