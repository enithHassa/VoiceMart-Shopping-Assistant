# app/services/recommendation_service.py - Recommendation engine

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json

from ..models import SearchHistory, ProductInteraction, UserPreference, Recommendation, User
from ..database import get_db

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    def track_product_interaction(
        self,
        user_id: str,
        product_id: str,
        product_title: str,
        product_category: Optional[str],
        product_brand: Optional[str],
        product_price: Optional[float],
        source: str,
        interaction_type: str,
        search_query: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ProductInteraction:
        """Track user interaction with a product"""
        try:
            # Convert user_id to UUID
            import uuid
            try:
                if isinstance(user_id, str) and len(user_id) == 36 and '-' in user_id:
                    user_uuid = uuid.UUID(user_id)
                else:
                    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
            except (ValueError, TypeError):
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
            
            interaction = ProductInteraction(
                user_id=user_uuid,
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
            
            self.db.add(interaction)
            self.db.commit()
            self.db.refresh(interaction)
            
            logger.info(f"Tracked {interaction_type} for user {user_id}: {product_title}")
            return interaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to track product interaction: {e}")
            raise
    
    def generate_search_suggestions(self, user_id: str, current_query: str = "", limit: int = 5) -> List[str]:
        """Generate search suggestions based on user's history and preferences"""
        try:
            # Convert user_id to UUID
            import uuid
            try:
                if isinstance(user_id, str) and len(user_id) == 36 and '-' in user_id:
                    user_uuid = uuid.UUID(user_id)
                else:
                    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
            except (ValueError, TypeError):
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
            
            # Get user's search history
            search_history = self.db.execute(
                select(SearchHistory.query)
                .where(SearchHistory.user_id == user_uuid)
                .order_by(desc(SearchHistory.timestamp))
                .limit(50)
            ).scalars().all()
            
            if not search_history:
                return self._get_popular_searches(limit)
            
            # Use TF-IDF to find similar queries
            if current_query:
                search_history.append(current_query)
            
            # Create TF-IDF matrix
            tfidf_matrix = self.vectorizer.fit_transform(search_history)
            
            if current_query:
                # Find similar queries to current input
                current_vector = self.vectorizer.transform([current_query])
                similarities = cosine_similarity(current_vector, tfidf_matrix[:-1]).flatten()
                
                # Get most similar queries
                similar_indices = np.argsort(similarities)[::-1][:limit]
                suggestions = [search_history[i] for i in similar_indices if similarities[i] > 0.1]
            else:
                # Get most frequent queries
                query_counts = {}
                for query in search_history:
                    query_counts[query] = query_counts.get(query, 0) + 1
                
                suggestions = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
                suggestions = [query for query, count in suggestions]
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate search suggestions: {e}")
            return self._get_popular_searches(limit)
    
    def generate_product_recommendations(
        self, 
        user_id: str, 
        current_query: str = "", 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate product recommendations based on user behavior"""
        try:
            # Get user's interaction history
            interactions = self.db.execute(
                select(ProductInteraction)
                .where(ProductInteraction.user_id == user_id)
                .order_by(desc(ProductInteraction.timestamp))
                .limit(100)
            ).scalars().all()
            
            if not interactions:
                return self._get_trending_products(limit)
            
            # Analyze user preferences
            preferences = self._analyze_user_preferences(user_id, interactions)
            
            # Generate recommendations based on preferences
            recommendations = []
            
            # Category-based recommendations
            if preferences.get('categories'):
                for category, score in preferences['categories'].items():
                    if score > 0.3:  # Threshold for preference
                        cat_recs = self._get_products_by_category(category, limit=3)
                        recommendations.extend(cat_recs)
            
            # Brand-based recommendations
            if preferences.get('brands'):
                for brand, score in preferences['brands'].items():
                    if score > 0.3:
                        brand_recs = self._get_products_by_brand(brand, limit=2)
                        recommendations.extend(brand_recs)
            
            # Price range recommendations
            if preferences.get('price_range'):
                price_min, price_max = preferences['price_range']
                price_recs = self._get_products_by_price_range(price_min, price_max, limit=3)
                recommendations.extend(price_recs)
            
            # Remove duplicates and limit results
            seen_products = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec['product_id'] not in seen_products:
                    seen_products.add(rec['product_id'])
                    unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break
            
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate product recommendations: {e}")
            return self._get_trending_products(limit)
    
    def _analyze_user_preferences(self, user_id: str, interactions: List[ProductInteraction]) -> Dict[str, Any]:
        """Analyze user preferences from interaction history"""
        preferences = {
            'categories': {},
            'brands': {},
            'price_range': None,
            'sources': {}
        }
        
        prices = []
        
        for interaction in interactions:
            # Category preferences
            if interaction.product_category:
                category = interaction.product_category.lower()
                weight = self._get_interaction_weight(interaction.interaction_type)
                preferences['categories'][category] = preferences['categories'].get(category, 0) + weight
            
            # Brand preferences
            if interaction.product_brand:
                brand = interaction.product_brand.lower()
                weight = self._get_interaction_weight(interaction.interaction_type)
                preferences['brands'][brand] = preferences['brands'].get(brand, 0) + weight
            
            # Price range
            if interaction.product_price:
                prices.append(interaction.product_price)
            
            # Source preferences
            source = interaction.source.lower()
            weight = self._get_interaction_weight(interaction.interaction_type)
            preferences['sources'][source] = preferences['sources'].get(source, 0) + weight
        
        # Normalize preferences
        for pref_type in ['categories', 'brands', 'sources']:
            total = sum(preferences[pref_type].values())
            if total > 0:
                preferences[pref_type] = {
                    k: v / total for k, v in preferences[pref_type].items()
                }
        
        # Calculate price range
        if prices:
            prices.sort()
            q25 = prices[int(len(prices) * 0.25)]
            q75 = prices[int(len(prices) * 0.75)]
            preferences['price_range'] = (q25, q75)
        
        return preferences
    
    def _get_interaction_weight(self, interaction_type: str) -> float:
        """Get weight for different interaction types"""
        weights = {
            'view': 1.0,
            'click': 2.0,
            'search': 1.5,
            'purchase': 5.0
        }
        return weights.get(interaction_type, 1.0)
    
    def _get_popular_searches(self, limit: int) -> List[str]:
        """Get popular searches across all users"""
        try:
            result = self.db.execute(
                select(
                    SearchHistory.query,
                    func.count().label('count')
                )
                .group_by(SearchHistory.query)
                .order_by(desc('count'))
                .limit(limit)
            ).all()
            
            return [row.query for row in result]
        except Exception as e:
            logger.error(f"Failed to get popular searches: {e}")
            return ["electronics", "clothing", "books", "home", "sports"]
    
    def _get_trending_products(self, limit: int) -> List[Dict[str, Any]]:
        """Get trending products across all users"""
        # This would typically query a products table
        # For now, return mock trending products
        return [
            {
                "product_id": f"trending_{i}",
                "title": f"Trending Product {i}",
                "price": 99.99 + i * 10,
                "source": "amazon",
                "category": "electronics",
                "recommendation_score": 0.9 - i * 0.1
            }
            for i in range(limit)
        ]
    
    def _get_products_by_category(self, category: str, limit: int) -> List[Dict[str, Any]]:
        """Get products by category (mock implementation)"""
        return [
            {
                "product_id": f"cat_{category}_{i}",
                "title": f"{category.title()} Product {i}",
                "price": 50.0 + i * 20,
                "source": "amazon",
                "category": category,
                "recommendation_score": 0.8
            }
            for i in range(limit)
        ]
    
    def _get_products_by_brand(self, brand: str, limit: int) -> List[Dict[str, Any]]:
        """Get products by brand (mock implementation)"""
        return [
            {
                "product_id": f"brand_{brand}_{i}",
                "title": f"{brand.title()} Product {i}",
                "price": 75.0 + i * 15,
                "source": "amazon",
                "brand": brand,
                "recommendation_score": 0.7
            }
            for i in range(limit)
        ]
    
    def _get_products_by_price_range(self, min_price: float, max_price: float, limit: int) -> List[Dict[str, Any]]:
        """Get products by price range (mock implementation)"""
        return [
            {
                "product_id": f"price_{i}",
                "title": f"Product in Price Range {i}",
                "price": min_price + (max_price - min_price) * (i / limit),
                "source": "amazon",
                "recommendation_score": 0.6
            }
            for i in range(limit)
        ]
    
    def cache_recommendations(
        self, 
        user_id: str, 
        recommendation_type: str, 
        recommendations: List[Any],
        expires_hours: int = 24
    ) -> Recommendation:
        """Cache recommendations for performance"""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            cached_rec = Recommendation(
                user_id=user_id,
                recommendation_type=recommendation_type,
                recommendations=recommendations,
                expires_at=expires_at,
                model_version="v1.0"
            )
            
            self.db.add(cached_rec)
            self.db.commit()
            self.db.refresh(cached_rec)
            
            return cached_rec
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cache recommendations: {e}")
            raise
    
    def get_cached_recommendations(
        self, 
        user_id: str, 
        recommendation_type: str
    ) -> Optional[List[Any]]:
        """Get cached recommendations if still valid"""
        try:
            result = self.db.execute(
                select(Recommendation)
                .where(
                    Recommendation.user_id == user_id,
                    Recommendation.recommendation_type == recommendation_type,
                    Recommendation.expires_at > datetime.utcnow()
                )
                .order_by(desc(Recommendation.generated_at))
                .limit(1)
            ).scalar_one_or_none()
            
            if result:
                return result.recommendations
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached recommendations: {e}")
            return None
