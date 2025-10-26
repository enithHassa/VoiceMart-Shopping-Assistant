# app/services/user_service.py - User management service

from sqlalchemy.orm import Session
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from ..models import User
from ..database import get_db

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-change-in-production"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, email: str, name: str, password: str, phone: Optional[str] = None) -> User:
        """Create a new user with hashed password"""
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Hash password
            hashed_password = pwd_context.hash(password)
            
            # Create user
            user = User(
                email=email,
                name=name,
                password_hash=hashed_password,
                phone=phone,
                preferences={}
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Created user: {email}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = self.get_user_by_email(email)
            if not user:
                return None
            
            if not pwd_context.verify(password, user.password_hash):
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = self.db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            result = self.db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    def update_user_profile(self, user_id: str, name: Optional[str] = None, phone: Optional[str] = None) -> Optional[User]:
        """Update user profile"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            if name is not None:
                user.name = name
            if phone is not None:
                user.phone = phone
            
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Updated user profile: {user.email}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user profile: {e}")
            return None
    
    def get_all_users(self) -> List[User]:
        """Get all users (for debugging)"""
        try:
            result = self.db.execute(select(User))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.preferences = preferences
            self.db.commit()
            
            logger.info(f"Updated preferences for user: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user preferences: {e}")
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None
