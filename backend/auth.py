# backend/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from backend.config import config
from backend.database import db
from typing import Optional, Dict

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str, role: str) -> Optional[Dict]:
    """Authenticate user from database"""
    if role == "admin":
        query = "SELECT UserId as id, UserName as email, Password as password FROM user_master WHERE UserName = %s"
        result = db.execute_query(query, (email,))
        
        if result and verify_password(password, result[0]['password']):
            return {
                "id": result[0]['id'],
                "email": result[0]['email'],
                "role": "admin",
                "name": "Administrator"
            }
    
    elif role == "teacher":
        query = "SELECT fac_id as id, email, name FROM facultyreg WHERE email = %s"
        result = db.execute_query(query, (email,))
        
        # Check in user_master for password
        user_query = "SELECT Password FROM user_master WHERE UserName = %s"
        user_result = db.execute_query(user_query, (email,))
        
        if result and user_result and verify_password(password, user_result[0]['Password']):
            return {
                "id": result[0]['id'],
                "email": result[0]['email'],
                "role": "teacher",
                "name": result[0]['name']
            }
    
    elif role == "student":
        # You may need to create a students table
        query = "SELECT UserId as id, UserName as email, Password as password FROM user_master WHERE UserName = %s"
        result = db.execute_query(query, (email,))
        
        if result and verify_password(password, result[0]['password']):
            return {
                "id": result[0]['id'],
                "email": result[0]['email'],
                "role": "student",
                "name": "Student"
            }
    
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict]:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except JWTError:
        return None