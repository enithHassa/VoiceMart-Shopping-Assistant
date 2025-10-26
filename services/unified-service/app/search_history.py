# app/search_history.py - Search history management

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger("search_history")

# In-memory storage for demo purposes
# In production, this would be stored in a database
_search_history: Dict[str, List[Dict[str, Any]]] = {}

class SearchHistoryItem:
    def __init__(
        self,
        user_id: str,
        query: str,
        sources: List[str],
        result_count: int,
        timestamp: Optional[float] = None
    ):
        self.id = f"search_{int((timestamp or datetime.now().timestamp()) * 1000)}_{hash(query) % 10000}"
        self.user_id = user_id
        self.query = query
        self.sources = sources
        self.result_count = result_count
        self.timestamp = timestamp or datetime.now().timestamp()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "query": self.query,
            "sources": self.sources,
            "result_count": self.result_count,
            "timestamp": self.timestamp
        }

def save_search_history(
    user_id: str,
    query: str,
    sources: List[str],
    result_count: int
) -> SearchHistoryItem:
    """Save a search to the user's history"""
    try:
        # Create new history item
        history_item = SearchHistoryItem(
            user_id=user_id,
            query=query,
            sources=sources,
            result_count=result_count
        )
        
        # Get existing history for user
        if user_id not in _search_history:
            _search_history[user_id] = []
        
        # Remove duplicate searches (same query and sources)
        _search_history[user_id] = [
            item for item in _search_history[user_id]
            if not (item["query"] == query and item["sources"] == sources)
        ]
        
        # Add new item at the beginning
        _search_history[user_id].insert(0, history_item.to_dict())
        
        # Keep only last 50 searches per user
        _search_history[user_id] = _search_history[user_id][:50]
        
        logger.info(f"Saved search history for user {user_id}: {query}")
        return history_item
        
    except Exception as e:
        logger.error(f"Failed to save search history: {e}")
        raise

def get_search_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get search history for a user"""
    try:
        if user_id not in _search_history:
            return []
        
        return _search_history[user_id][:limit]
        
    except Exception as e:
        logger.error(f"Failed to get search history: {e}")
        return []

def clear_search_history(user_id: str) -> bool:
    """Clear all search history for a user"""
    try:
        if user_id in _search_history:
            del _search_history[user_id]
            logger.info(f"Cleared search history for user {user_id}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Failed to clear search history: {e}")
        return False

def delete_search_history_item(user_id: str, item_id: str) -> bool:
    """Delete a specific search history item"""
    try:
        if user_id not in _search_history:
            return False
        
        original_length = len(_search_history[user_id])
        _search_history[user_id] = [
            item for item in _search_history[user_id]
            if item["id"] != item_id
        ]
        
        deleted = len(_search_history[user_id]) < original_length
        if deleted:
            logger.info(f"Deleted search history item {item_id} for user {user_id}")
        
        return deleted
        
    except Exception as e:
        logger.error(f"Failed to delete search history item: {e}")
        return False

def get_search_analytics(user_id: str) -> Dict[str, Any]:
    """Get search analytics for a user"""
    try:
        if user_id not in _search_history:
            return {
                "total_searches": 0,
                "popular_queries": [],
                "popular_sources": [],
                "recent_activity": []
            }
        
        history = _search_history[user_id]
        
        # Count popular queries
        query_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        
        for item in history:
            query = item["query"]
            query_counts[query] = query_counts.get(query, 0) + 1
            
            for source in item["sources"]:
                source_counts[source] = source_counts.get(source, 0) + 1
        
        # Get top queries and sources
        popular_queries = sorted(
            query_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        popular_sources = sorted(
            source_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        return {
            "total_searches": len(history),
            "popular_queries": [{"query": q, "count": c} for q, c in popular_queries],
            "popular_sources": [{"source": s, "count": c} for s, c in popular_sources],
            "recent_activity": history[:5]  # Last 5 searches
        }
        
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        return {
            "total_searches": 0,
            "popular_queries": [],
            "popular_sources": [],
            "recent_activity": []
        }
