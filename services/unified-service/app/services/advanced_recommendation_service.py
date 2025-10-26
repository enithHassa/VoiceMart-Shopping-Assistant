# app/services/advanced_recommendation_service.py - Advanced recommendation engine

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func, and_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np
import json
import uuid
import requests
import asyncio

from ..models import SearchHistory, ProductInteraction, UserPreference, Recommendation, User
from ..database import get_db

logger = logging.getLogger(__name__)

class AdvancedRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.product_finder_url = "http://localhost:8003"  # Product finder service
        
    def generate_comprehensive_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate comprehensive product recommendations using multiple strategies"""
        try:
            # Convert user_id to UUID
            user_uuid = self._convert_user_id_to_uuid(user_id)
            
            # Get user data
            user_searches = self._get_user_search_history(user_uuid)
            user_interactions = self._get_user_interactions(user_uuid)
            
            # Strategy 1: Content-Based Recommendations (50%) - Use real product searches
            content_recs = self._generate_content_based_recommendations(user_searches, user_interactions, int(limit * 0.5))
            
            # Strategy 2: Popular Products (30%) - Search for popular items
            popular_recs = self._generate_popular_recommendations(int(limit * 0.3))
            
            # Strategy 3: Trending Products (20%) - From database interactions
            trending_recs = self._generate_trending_recommendations(user_interactions, int(limit * 0.2))
            
            # Combine and rank all recommendations
            all_recommendations = content_recs + popular_recs + trending_recs
            ranked_recommendations = self._rank_and_deduplicate_recommendations(all_recommendations, user_uuid)
            
            # If we don't have enough recommendations, fill with real product searches
            if len(ranked_recommendations) < limit:
                additional_recs = self._generate_additional_recommendations(limit - len(ranked_recommendations))
                ranked_recommendations.extend(additional_recs)
            
            return ranked_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive recommendations: {e}")
            return self._generate_popular_recommendations(limit)
    
    def _generate_content_based_recommendations(self, user_searches: List[str], user_interactions: List[ProductInteraction], limit: int) -> List[Dict[str, Any]]:
        """Generate recommendations based on user's search history and interactions"""
        try:
            if not user_searches and not user_interactions:
                return []
            
            # Extract keywords from user's search history
            search_keywords = []
            for search in user_searches:
                search_keywords.extend(search.lower().split())
            
            # Extract keywords from user's interactions
            interaction_keywords = []
            for interaction in user_interactions:
                if interaction.product_title:
                    interaction_keywords.extend(interaction.product_title.lower().split())
                if interaction.search_query:
                    interaction_keywords.extend(interaction.search_query.lower().split())
            
            # Combine all keywords
            all_keywords = search_keywords + interaction_keywords
            
            if not all_keywords:
                return []
            
            # Find most common keywords
            keyword_counts = {}
            for keyword in all_keywords:
                if len(keyword) > 2:  # Filter out short words
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Generate search queries from top keywords
            search_queries = []
            for keyword, count in top_keywords:
                search_queries.append(keyword)
                # Create compound queries
                for other_keyword, other_count in top_keywords:
                    if keyword != other_keyword:
                        search_queries.append(f"{keyword} {other_keyword}")
            
            # Search for products using these queries
            recommendations = []
            for query in search_queries[:3]:  # Limit to top 3 queries
                try:
                    products = self._search_products_from_finder(query, limit=limit//3)
                    for product in products:
                        product['recommendation_type'] = 'content_based'
                        product['recommendation_reason'] = f"Based on your interest in '{query}'"
                        product['recommendation_score'] = self._calculate_content_score(product, all_keywords)
                        # Ensure all required fields are present
                        if 'image_url' not in product or not product['image_url']:
                            product['image_url'] = 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop'
                        if 'currency' not in product:
                            product['currency'] = 'USD'
                        if 'rating' not in product:
                            product['rating'] = 4.2
                        if 'url' not in product:
                            product['url'] = f"https://{product.get('source', 'amazon')}.com/product/{product.get('id', 'unknown')}"
                        recommendations.append(product)
                except Exception as e:
                    logger.warning(f"Failed to search products for query '{query}': {e}")
                    continue
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate content-based recommendations: {e}")
            return []
    
    def _generate_collaborative_recommendations(self, user_uuid: uuid.UUID, limit: int) -> List[Dict[str, Any]]:
        """Generate recommendations based on similar users' behavior"""
        try:
            # Get users with similar search patterns
            similar_users = self._find_similar_users(user_uuid)
            
            if not similar_users:
                return []
            
            # Get products that similar users interacted with but current user hasn't
            user_interactions = self._get_user_interactions(user_uuid)
            user_product_ids = {interaction.product_id for interaction in user_interactions}
            
            recommendations = []
            for similar_user_id in similar_users[:5]:  # Top 5 similar users
                similar_user_interactions = self._get_user_interactions(similar_user_id)
                
                for interaction in similar_user_interactions:
                    if interaction.product_id not in user_product_ids:
                        # This is a product the similar user liked but current user hasn't seen
                        product_data = {
                            'id': interaction.product_id,
                            'title': interaction.product_title,
                            'price': interaction.product_price or 0,
                            'currency': 'USD',
                            'category': interaction.product_category,
                            'brand': interaction.product_brand,
                            'source': interaction.source,
                            'image_url': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop',
                            'rating': 4.3,
                            'url': f'https://{interaction.source}.com/product/{interaction.product_id}',
                            'recommendation_type': 'collaborative',
                            'recommendation_reason': f"Users with similar interests also viewed this",
                            'recommendation_score': 0.7,  # Base score for collaborative
                        }
                        recommendations.append(product_data)
            
            # Remove duplicates and sort by score
            unique_recommendations = self._deduplicate_recommendations(recommendations)
            return unique_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate collaborative recommendations: {e}")
            return []
    
    def _generate_trending_recommendations(self, user_interactions: List[ProductInteraction], limit: int) -> List[Dict[str, Any]]:
        """Generate recommendations based on trending products"""
        try:
            # Get trending products from recent interactions across all users
            trending_products = self.db.execute(
                select(
                    ProductInteraction.product_id,
                    ProductInteraction.product_title,
                    ProductInteraction.product_price,
                    ProductInteraction.product_category,
                    ProductInteraction.product_brand,
                    ProductInteraction.source,
                    func.count(ProductInteraction.id).label('interaction_count')
                )
                .where(ProductInteraction.timestamp >= datetime.utcnow() - timedelta(days=7))
                .group_by(
                    ProductInteraction.product_id,
                    ProductInteraction.product_title,
                    ProductInteraction.product_price,
                    ProductInteraction.product_category,
                    ProductInteraction.product_brand,
                    ProductInteraction.source
                )
                .order_by(desc('interaction_count'))
                .limit(limit * 2)
            ).all()
            
            recommendations = []
            for product in trending_products:
                product_data = {
                    'id': product.product_id,
                    'title': product.product_title,
                    'price': product.product_price or 0,
                    'currency': 'USD',
                    'category': product.product_category,
                    'brand': product.product_brand,
                    'source': product.source,
                    'image_url': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop',
                    'rating': 4.2,
                    'url': f'https://{product.source}.com/product/{product.product_id}',
                    'recommendation_type': 'trending',
                    'recommendation_reason': f"Trending product with {product.interaction_count} recent views",
                    'recommendation_score': min(0.9, 0.5 + (product.interaction_count * 0.1)),
                }
                recommendations.append(product_data)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate trending recommendations: {e}")
            return []
    
    def _generate_category_recommendations(self, user_searches: List[str], limit: int) -> List[Dict[str, Any]]:
        """Generate recommendations based on user's preferred categories"""
        try:
            if not user_searches:
                return []
            
            # Extract categories from search queries
            categories = set()
            for search in user_searches:
                # Simple category extraction (in real system, use NLP)
                search_lower = search.lower()
                if any(word in search_lower for word in ['laptop', 'computer', 'pc']):
                    categories.add('electronics')
                if any(word in search_lower for word in ['phone', 'smartphone', 'mobile']):
                    categories.add('electronics')
                if any(word in search_lower for word in ['headphone', 'earphone', 'audio']):
                    categories.add('audio')
                if any(word in search_lower for word in ['shirt', 'clothes', 'fashion']):
                    categories.add('fashion')
                if any(word in search_lower for word in ['book', 'novel', 'reading']):
                    categories.add('books')
            
            if not categories:
                return []
            
            # Search for products in these categories
            recommendations = []
            for category in list(categories)[:2]:  # Limit to top 2 categories
                try:
                    products = self._search_products_from_finder(category, limit=limit//len(categories))
                    for product in products:
                        product['recommendation_type'] = 'category_based'
                        product['recommendation_reason'] = f"Popular in {category} category"
                        product['recommendation_score'] = 0.6
                        # Ensure all required fields are present
                        if 'image_url' not in product or not product['image_url']:
                            product['image_url'] = 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop'
                        if 'currency' not in product:
                            product['currency'] = 'USD'
                        if 'rating' not in product:
                            product['rating'] = 4.1
                        if 'url' not in product:
                            product['url'] = f"https://{product.get('source', 'amazon')}.com/product/{product.get('id', 'unknown')}"
                        recommendations.append(product)
                except Exception as e:
                    logger.warning(f"Failed to search products for category '{category}': {e}")
                    continue
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate category recommendations: {e}")
            return []
    
    def _search_products_from_finder(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for products using the product finder service"""
        try:
            # Call the product finder service
            response = requests.post(
                f"{self.product_finder_url}/v1/products:search",
                json={
                    "query": query,
                    "limit": limit,
                    "sources": ["amazon", "ebay", "walmart"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                # Ensure all products have proper URLs
                for product in products:
                    if not product.get('url') or 'example.com' in product.get('url', ''):
                        # Generate a more realistic URL based on source
                        source = product.get('source', 'amazon')
                        product_id = product.get('id', 'unknown')
                        title = product.get('title', '').lower().replace(' ', '-')
                        
                        if source == 'amazon':
                            product['url'] = f"https://www.amazon.com/dp/{product_id}"
                        elif source == 'ebay':
                            product['url'] = f"https://www.ebay.com/itm/{product_id}"
                        elif source == 'walmart':
                            product['url'] = f"https://www.walmart.com/ip/{product_id}"
                        else:
                            product['url'] = f"https://www.amazon.com/dp/{product_id}"
                
                return products
            else:
                logger.warning(f"Product finder returned status {response.status_code}")
                return []
                
        except Exception as e:
            logger.warning(f"Failed to call product finder service: {e}")
            return []
    
    def _find_similar_users(self, user_uuid: uuid.UUID) -> List[uuid.UUID]:
        """Find users with similar search patterns"""
        try:
            # Get current user's search history
            user_searches = self._get_user_search_history(user_uuid)
            
            if not user_searches:
                return []
            
            # Get all other users' search histories
            all_users = self.db.execute(
                select(SearchHistory.user_id)
                .where(SearchHistory.user_id != user_uuid)
                .distinct()
            ).scalars().all()
            
            similar_users = []
            for other_user_id in all_users:
                other_searches = self._get_user_search_history(other_user_id)
                
                # Calculate similarity using Jaccard similarity
                similarity = self._calculate_jaccard_similarity(user_searches, other_searches)
                
                if similarity > 0.3:  # Threshold for similarity
                    similar_users.append((other_user_id, similarity))
            
            # Sort by similarity and return user IDs
            similar_users.sort(key=lambda x: x[1], reverse=True)
            return [user_id for user_id, _ in similar_users[:10]]
            
        except Exception as e:
            logger.error(f"Failed to find similar users: {e}")
            return []
    
    def _calculate_jaccard_similarity(self, list1: List[str], list2: List[str]) -> float:
        """Calculate Jaccard similarity between two lists"""
        if not list1 or not list2:
            return 0.0
        
        set1 = set(list1)
        set2 = set(list2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_content_score(self, product: Dict[str, Any], user_keywords: List[str]) -> float:
        """Calculate recommendation score based on content similarity"""
        try:
            product_text = f"{product.get('title', '')} {product.get('description', '')} {product.get('category', '')}"
            product_text = product_text.lower()
            
            # Count keyword matches
            matches = sum(1 for keyword in user_keywords if keyword in product_text)
            
            # Calculate score based on matches
            if len(user_keywords) > 0:
                score = min(0.9, 0.3 + (matches / len(user_keywords)) * 0.6)
            else:
                score = 0.3
            
            return score
            
        except Exception as e:
            logger.error(f"Failed to calculate content score: {e}")
            return 0.3
    
    def _rank_and_deduplicate_recommendations(self, recommendations: List[Dict[str, Any]], user_uuid: uuid.UUID) -> List[Dict[str, Any]]:
        """Rank and deduplicate recommendations"""
        try:
            # Remove duplicates based on product ID
            unique_recommendations = self._deduplicate_recommendations(recommendations)
            
            # Sort by recommendation score
            unique_recommendations.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
            
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"Failed to rank recommendations: {e}")
            return recommendations
    
    def _deduplicate_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate recommendations"""
        seen_ids = set()
        unique_recommendations = []
        
        for rec in recommendations:
            product_id = rec.get('id')
            if product_id and product_id not in seen_ids:
                seen_ids.add(product_id)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _get_user_search_history(self, user_uuid: uuid.UUID) -> List[str]:
        """Get user's search history"""
        try:
            searches = self.db.execute(
                select(SearchHistory.query)
                .where(SearchHistory.user_id == user_uuid)
                .order_by(desc(SearchHistory.timestamp))
                .limit(50)
            ).scalars().all()
            
            return list(searches)
            
        except Exception as e:
            logger.error(f"Failed to get user search history: {e}")
            return []
    
    def _get_user_interactions(self, user_uuid: uuid.UUID) -> List[ProductInteraction]:
        """Get user's product interactions"""
        try:
            interactions = self.db.execute(
                select(ProductInteraction)
                .where(ProductInteraction.user_id == user_uuid)
                .order_by(desc(ProductInteraction.timestamp))
                .limit(100)
            ).scalars().all()
            
            return list(interactions)
            
        except Exception as e:
            logger.error(f"Failed to get user interactions: {e}")
            return []
    
    def _convert_user_id_to_uuid(self, user_id: str) -> uuid.UUID:
        """Convert string user_id to UUID"""
        try:
            if isinstance(user_id, str) and len(user_id) == 36 and '-' in user_id:
                return uuid.UUID(user_id)
            else:
                return uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
        except (ValueError, TypeError):
            return uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
    
    def _get_fallback_recommendations(self, limit: int) -> List[Dict[str, Any]]:
        """Get fallback recommendations when other methods fail"""
        fallback_products = [
            {
                'id': 'fallback_laptop',
                'title': 'Dell XPS 13 Laptop - Premium Quality',
                'price': 1299.99,
                'currency': 'USD',
                'category': 'electronics',
                'brand': 'Dell',
                'source': 'amazon',
                'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=400&fit=crop',
                'rating': 4.5,
                'url': 'https://www.amazon.com/dp/B08N5WRWNW',
                'recommendation_type': 'content_based',
                'recommendation_reason': 'Popular laptop with excellent reviews',
                'recommendation_score': 0.8,
            },
            {
                'id': 'fallback_headphones',
                'title': 'Sony WH-1000XM5 Wireless Headphones',
                'price': 399.99,
                'currency': 'USD',
                'category': 'audio',
                'brand': 'Sony',
                'source': 'ebay',
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop',
                'rating': 4.6,
                'url': 'https://www.ebay.com/itm/334123456789',
                'recommendation_type': 'collaborative',
                'recommendation_reason': 'Users with similar interests also viewed this',
                'recommendation_score': 0.7,
            },
            {
                'id': 'fallback_phone',
                'title': 'iPhone 15 Pro - Latest Model',
                'price': 999.99,
                'currency': 'USD',
                'category': 'electronics',
                'brand': 'Apple',
                'source': 'walmart',
                'image_url': 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400&h=400&fit=crop',
                'rating': 4.7,
                'url': 'https://www.walmart.com/ip/123456789',
                'recommendation_type': 'trending',
                'recommendation_reason': 'Trending product with high demand',
                'recommendation_score': 0.9,
            },
            {
                'id': 'fallback_gaming',
                'title': 'PlayStation 5 Console - Gaming',
                'price': 499.99,
                'currency': 'USD',
                'category': 'gaming',
                'brand': 'Sony',
                'source': 'amazon',
                'image_url': 'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=400&h=400&fit=crop',
                'rating': 4.8,
                'url': 'https://www.amazon.com/dp/B08H95Y452',
                'recommendation_type': 'category_based',
                'recommendation_reason': 'Popular in gaming category',
                'recommendation_score': 0.6,
            },
            {
                'id': 'fallback_keyboard',
                'title': 'Logitech MX Keys Wireless Keyboard',
                'price': 99.99,
                'currency': 'USD',
                'category': 'electronics',
                'brand': 'Logitech',
                'source': 'ebay',
                'image_url': 'https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=400&h=400&fit=crop',
                'rating': 4.4,
                'url': 'https://ebay.com/logitech-keyboard',
                'recommendation_type': 'content_based',
                'recommendation_reason': 'Based on your interest in electronics',
                'recommendation_score': 0.7,
            },
            {
                'id': 'fallback_mouse',
                'title': 'Logitech MX Master 3 Mouse',
                'price': 79.99,
                'currency': 'USD',
                'category': 'electronics',
                'brand': 'Logitech',
                'source': 'walmart',
                'image_url': 'https://images.unsplash.com/photo-1527864550417-7fd46fc67126?w=400&h=400&fit=crop',
                'rating': 4.5,
                'url': 'https://walmart.com/logitech-mouse',
                'recommendation_type': 'collaborative',
                'recommendation_reason': 'Similar users also purchased this',
                'recommendation_score': 0.6,
            },
            {
                'id': 'fallback_tablet',
                'title': 'iPad Air 5th Generation',
                'price': 599.99,
                'currency': 'USD',
                'category': 'electronics',
                'brand': 'Apple',
                'source': 'amazon',
                'image_url': 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&h=400&fit=crop',
                'rating': 4.6,
                'url': 'https://amazon.com/ipad-air',
                'recommendation_type': 'trending',
                'recommendation_reason': 'Trending tablet with great reviews',
                'recommendation_score': 0.8,
            },
            {
                'id': 'fallback_smartwatch',
                'title': 'Apple Watch Series 9',
                'price': 399.99,
                'currency': 'USD',
                'category': 'electronics',
                'brand': 'Apple',
                'source': 'ebay',
                'image_url': 'https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=400&h=400&fit=crop',
                'rating': 4.5,
                'url': 'https://ebay.com/apple-watch',
                'recommendation_type': 'category_based',
                'recommendation_reason': 'Popular in electronics category',
                'recommendation_score': 0.7,
            }
        ]
        
        return fallback_products[:limit]
    
    def _generate_popular_recommendations(self, limit: int) -> List[Dict[str, Any]]:
        """Generate recommendations based on popular product searches"""
        try:
            # Search for popular products
            popular_queries = ['laptop', 'smartphone', 'headphones', 'tablet', 'smartwatch']
            recommendations = []
            
            for query in popular_queries[:limit//2]:
                products = self._search_products_from_finder(query, limit=2)
                for product in products:
                    product['recommendation_type'] = 'popular'
                    product['recommendation_reason'] = f"Popular {query} with great reviews"
                    product['recommendation_score'] = 0.7
                    recommendations.append(product)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate popular recommendations: {e}")
            return []
    
    def _generate_additional_recommendations(self, limit: int) -> List[Dict[str, Any]]:
        """Generate additional recommendations using real product searches"""
        try:
            # Search for trending products
            trending_queries = ['gaming laptop', 'wireless earbuds', 'fitness tracker', 'bluetooth speaker']
            recommendations = []
            
            for query in trending_queries[:limit]:
                products = self._search_products_from_finder(query, limit=1)
                for product in products:
                    product['recommendation_type'] = 'trending'
                    product['recommendation_reason'] = f"Trending {query} with high demand"
                    product['recommendation_score'] = 0.8
                    recommendations.append(product)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate additional recommendations: {e}")
            return []
