# app/services/search_history_service.py - Search history management service

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import uuid

from ..models import SearchHistory, User
from ..database import get_db

logger = logging.getLogger(__name__)

class SearchHistoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def _convert_user_id_to_uuid(self, user_id: str) -> uuid.UUID:
        """Convert string user_id to UUID"""
        try:
            if isinstance(user_id, str) and len(user_id) == 36 and '-' in user_id:
                return uuid.UUID(user_id)
            else:
                return uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
        except (ValueError, TypeError):
            return uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}")
    
    def _ensure_user_exists(self, user_id: str) -> uuid.UUID:
        """Ensure user exists in database, create if not"""
        user_uuid = self._convert_user_id_to_uuid(user_id)
        
        # Check if user exists
        existing_user = self.db.execute(
            select(User).where(User.id == user_uuid)
        ).scalar_one_or_none()
        
        if not existing_user:
            # Create a minimal user record
            new_user = User(
                id=user_uuid,
                email=f"{user_id}@temp.voicemart.com",
                name=f"User {user_id}",
                password_hash=None  # No password for temp users
            )
            self.db.add(new_user)
            self.db.commit()
            logger.info(f"Created temporary user: {user_id}")
        
        return user_uuid
    
    def save_search_history(
        self, 
        user_id: str, 
        query: str, 
        sources: List[str], 
        result_count: int,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SearchHistory:
        """Save a search to user's history"""
        try:
            # Ensure user exists and get UUID
            user_uuid = self._ensure_user_exists(user_id)
            
            # Remove duplicate searches (same query and sources within last hour)
            recent_duplicate = self.db.execute(
                select(SearchHistory).where(
                    SearchHistory.user_id == user_uuid,
                    SearchHistory.query == query,
                    SearchHistory.sources == sources,
                    SearchHistory.timestamp >= datetime.utcnow() - timedelta(hours=1)
                )
            ).scalar_one_or_none()
            
            if recent_duplicate:
                # Update existing search timestamp
                recent_duplicate.timestamp = datetime.utcnow()
                recent_duplicate.result_count = result_count
                self.db.commit()
                return recent_duplicate
            
            # Create new search history entry
            search_history = SearchHistory(
                user_id=user_uuid,
                query=query,
                sources=sources,
                result_count=result_count,
                session_id=session_id,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            self.db.add(search_history)
            self.db.commit()
            self.db.refresh(search_history)
            
            logger.info(f"Saved search history for user {user_id}: {query}")
            return search_history
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save search history: {e}")
            raise
    
    def get_search_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get search history for a user"""
        try:
            # Convert string user_id to UUID
            user_uuid = self._convert_user_id_to_uuid(user_id)
            
            result = self.db.execute(
                select(SearchHistory)
                .where(SearchHistory.user_id == user_uuid)
                .order_by(desc(SearchHistory.timestamp))
                .limit(limit)
            )
            
            search_history = result.scalars().all()
            return [item.to_dict() for item in search_history]
            
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            return []
    
    def clear_search_history(self, user_id: str) -> bool:
        """Clear all search history for a user"""
        try:
            user_uuid = self._convert_user_id_to_uuid(user_id)
            self.db.execute(
                select(SearchHistory).where(SearchHistory.user_id == user_uuid).delete()
            )
            self.db.commit()
            
            logger.info(f"Cleared search history for user: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to clear search history: {e}")
            return False
    
    def delete_search_history_item(self, user_id: str, item_id: str) -> bool:
        """Delete a specific search history item"""
        try:
            user_uuid = self._convert_user_id_to_uuid(user_id)
            result = self.db.execute(
                select(SearchHistory).where(
                    SearchHistory.id == item_id,
                    SearchHistory.user_id == user_uuid
                ).delete()
            )
            
            if result.rowcount > 0:
                self.db.commit()
                logger.info(f"Deleted search history item: {item_id}")
                return True
            else:
                logger.warning(f"Search history item not found: {item_id}")
                return False
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete search history item: {e}")
            return False
    
    def get_search_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get search analytics for a user"""
        try:
            user_uuid = self._convert_user_id_to_uuid(user_id)
            
            # Total searches
            total_searches = self.db.execute(
                select(func.count(SearchHistory.id)).where(SearchHistory.user_id == user_uuid)
            ).scalar()
            
            # Unique queries
            unique_queries = self.db.execute(
                select(func.count(func.distinct(SearchHistory.query)))
                .where(SearchHistory.user_id == user_uuid)
            ).scalar()
            
            # Most frequent sources
            source_counts = self.db.execute(
                select(
                    func.unnest(SearchHistory.sources).label('source'),
                    func.count().label('count')
                )
                .where(SearchHistory.user_id == user_uuid)
                .group_by('source')
                .order_by(desc('count'))
            ).all()
            
            # Last search timestamp
            last_search = self.db.execute(
                select(SearchHistory.timestamp)
                .where(SearchHistory.user_id == user_uuid)
                .order_by(desc(SearchHistory.timestamp))
                .limit(1)
            ).scalar()
            
            return {
                "total_searches": total_searches or 0,
                "unique_queries": unique_queries or 0,
                "most_frequent_sources": [(row.source, row.count) for row in source_counts],
                "last_search_timestamp": last_search.isoformat() if last_search else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {
                "total_searches": 0,
                "unique_queries": 0,
                "most_frequent_sources": [],
                "last_search_timestamp": None,
            }
    
    def get_search_suggestions(self, user_id: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on user's history"""
        try:
            user_uuid = self._convert_user_id_to_uuid(user_id)
            
            # Get recent unique queries
            result = self.db.execute(
                select(func.distinct(SearchHistory.query))
                .where(SearchHistory.user_id == user_uuid)
                .order_by(desc(SearchHistory.timestamp))
                .limit(limit * 2)  # Get more to filter
            )
            
            suggestions = []
            for row in result:
                query = row[0]
                if len(query) > 2 and query not in suggestions:  # Filter meaningful queries
                    suggestions.append(query)
                if len(suggestions) >= limit:
                    break
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
