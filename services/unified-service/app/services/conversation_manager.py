"""
Conversation Manager - Manages voice conversation state and context
"""
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """Represents the current state of a conversation"""
    session_id: str
    user_id: Optional[str]
    query: str
    intent: str  # "search", "filter", "refine"
    category: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None
    brand: Optional[str] = None
    question: Optional[str] = None  # Follow-up question to ask
    context: Dict[str, Any] = None  # Additional context
    ready_to_search: bool = False  # Whether we have enough info to search
    created_at: datetime = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.created_at is None:
            self.created_at = datetime.now()

# In-memory conversation storage (for production, use Redis or database)
_conversations: Dict[str, ConversationState] = {}
_session_timeout = timedelta(minutes=30)

def get_conversation(session_id: str) -> Optional[ConversationState]:
    """Get conversation state for a session"""
    conv = _conversations.get(session_id)
    
    if conv and datetime.now() - conv.created_at < _session_timeout:
        return conv
    
    if conv:
        # Remove expired conversation
        del _conversations[session_id]
        logger.info(f"Expired conversation for session {session_id}")
    
    return None

def save_conversation(conversation: ConversationState):
    """Save conversation state"""
    _conversations[conversation.session_id] = conversation
    logger.info(f"Saved conversation for session {conversation.session_id}")

def clear_conversation(session_id: str):
    """Clear conversation state"""
    if session_id in _conversations:
        del _conversations[session_id]
        logger.info(f"Cleared conversation for session {session_id}")

def has_missing_context(state: ConversationState) -> bool:
    """Check if conversation has missing critical context"""
    if not state.category and state.intent == "search":
        return True
    if not state.price_range and state.intent == "search":
        return True
    return False

def extract_entities(query: str) -> Dict[str, Any]:
    """Extract entities from user query using pattern matching"""
    entities = {
        "category": None,
        "price_range": None,
        "brand": None,
        "keywords": []
    }
    
    query_lower = query.lower()
    
    # Extract category
    categories = {
        "laptop": ["laptop", "laptops", "notebook", "notebooks", "computer", "pc", "macbook"],
        "phone": ["phone", "phones", "smartphone", "smartphones", "mobile", "iphone", "android"],
        "headphone": ["headphone", "headphones", "earbuds", "earphones", "audio"],
        "tablet": ["tablet", "tablets", "ipad"],
        "gaming": ["gaming", "gaming laptop", "gaming pc", "game"],
        "electronics": ["electronic", "electronics", "device", "devices"],
        "camera": ["camera", "cameras", "photography"],
        "tv": ["tv", "television", "tv set", "smart tv"]
    }
    
    for cat, keywords in categories.items():
        if any(keyword in query_lower for keyword in keywords):
            entities["category"] = cat
            break
    
    # Extract price range
    import re
    
    # Try to find price patterns like "$500", "500 dollars", etc.
    price_patterns = [
        r'\$(\d+(?:,\d+)*(?:\.\d+)?)',  # $500, $1,000
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:dollars?|bucks)',  # 500 dollars
        r'(?:under|below|over|above|around|about)\s*\$?(\d+(?:,\d+)*(?:\.\d+)?)',  # under 500, over $1000
        r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)',  # $ 500 (with space)
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            try:
                price_str = matches[0].replace(",", "")
                price = float(price_str)
                
                # Determine if it's max or min based on context
                if any(word in query_lower for word in ["under", "below", "less than", "cheaper than", "maximum", "max"]):
                    entities["price_range"] = {"max": price}
                elif any(word in query_lower for word in ["over", "above", "more than", "expensive than", "minimum", "min"]):
                    entities["price_range"] = {"min": price}
                elif any(word in query_lower for word in ["around", "about", "approximately"]):
                    entities["price_range"] = {"min": price * 0.8, "max": price * 1.2}
                else:
                    # Default: treat as max price
                    entities["price_range"] = {"max": price}
            except (ValueError, IndexError):
                pass
            break
    
    # Extract brand
    brands = ["apple", "samsung", "dell", "hp", "lenovo", "asus", "msi", "acer", "sony"]
    for brand in brands:
        if brand in query_lower:
            entities["brand"] = brand
            break
    
    # Extract keywords (remaining words after removing entities)
    entities["keywords"] = [w for w in query_lower.split() if len(w) > 2]
    
    return entities

def generate_followup_question(state: ConversationState) -> Optional[str]:
    """Generate a follow-up question based on missing context"""
    if not state.category and state.intent == "search":
        return "What category are you looking for? (e.g., laptop, phone, headphones)"
    
    # For laptops, ask about type
    if state.category == "laptop" and state.price_range:
        if "gaming" not in state.context and "office" not in state.context:
            return "Do you prefer gaming or office laptops?"
    
    # For phones, ask about brand if price specified
    if state.category == "phone" and state.price_range:
        if not state.brand:
            return "Which brand? (e.g., Apple, Samsung, Google)"
    
    return None

def process_voice_query(session_id: str, user_id: Optional[str], transcript: str, reset: bool = False) -> Dict[str, Any]:
    """
    Process a voice query and return conversation response
    """
    if reset:
        clear_conversation(session_id)
    
    # Get or create conversation state
    state = get_conversation(session_id)
    
    if state is None:
        # New conversation
        intent = "search"
        entities = extract_entities(transcript)
        question = generate_followup_question(ConversationState(
            session_id=session_id,
            user_id=user_id,
            query=transcript,
            intent=intent,
            category=entities.get("category"),
            price_range=entities.get("price_range")
        ))
        
        state = ConversationState(
            session_id=session_id,
            user_id=user_id,
            query=transcript,
            intent=intent,
            category=entities.get("category"),
            price_range=entities.get("price_range"),
            brand=entities.get("brand"),
            question=question
        )
        save_conversation(state)
    else:
        # Continuing conversation - check if answering a question
        if state.question:
            # User is answering the previous question
            transcript_lower = transcript.lower()
            
            # Check for laptop preferences
            if "gaming" in transcript_lower:
                state.context["preference"] = "gaming"
                state.question = None
                state.ready_to_search = True
            elif "office" in transcript_lower or "work" in transcript_lower:
                state.context["preference"] = "office"
                state.question = None
                state.ready_to_search = True
            # Check for brand answers
            elif "brand" in state.question.lower():
                # Extract brand from answer
                brands = ["apple", "samsung", "google", "xiaomi", "oneplus", "motorola", "nokia", "sony"]
                for brand in brands:
                    if brand in transcript_lower:
                        state.brand = brand
                        state.question = None
                        state.ready_to_search = True
                        break
                # If no brand found, still mark as ready (user said "any" or skip)
                if not state.brand:
                    state.question = None
                    state.ready_to_search = True
            
            # Generate new question or proceed
            if state.question is None:
                # No more questions, ready to search
                pass
            else:
                new_question = generate_followup_question(state)
                state.question = new_question
        else:
            # New query in same session
            entities = extract_entities(transcript)
            if entities.get("category"):
                state.category = entities.get("category")
            if entities.get("price_range"):
                state.price_range = entities.get("price_range")
            if entities.get("brand"):
                state.brand = entities.get("brand")
            
            state.query = transcript
            state.question = generate_followup_question(state)
        
        save_conversation(state)
    
    # Prepare response
    response = {
        "transcript": transcript,
        "query": state.query,
        "question": state.question,
        "ready_to_search": state.question is None
    }
    
    # Add search parameters if ready
    if state.question is None:
        response["search_params"] = {
            "query": state.query,
            "category": state.category,
            "price_range": state.price_range,
            "brand": state.brand,
            "context": state.context
        }
    
    return response

