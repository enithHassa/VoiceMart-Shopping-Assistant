# Simple mock processor for testing
from typing import Dict, Any, Optional

def process_query(query_text: str, user_id: Optional[str] = None, locale: str = "en-US") -> Dict[str, Any]:
    """Simple mock query processor that returns basic results."""
        return {
        "intent": "search",
        "confidence": 0.8,
        "slots": {
            "query": query_text,
            "raw": query_text
        },
        "reply": f"I'll help you search for: {query_text}",
        "action": {
            "type": "search",
            "params": {
                "query": query_text,
                "raw": query_text
            }
        },
        "user_id": user_id,
        "locale": locale
    }