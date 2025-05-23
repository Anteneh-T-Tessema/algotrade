#!/usr/bin/env python3
"""
Production-ready API server for strategy analysis dashboard.
Features:
- Health checks and monitoring
- Request validation
- Proper logging
- Error handling
- Configuration management
"""
import os
import sys
import json
import logging
import time
import hashlib
import hmac
import secrets
import base64
import pyotp
import jwt
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict, deque
from fastapi import FastAPI, HTTPException, Depends, Request, status, Security, Header, Form, Body, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
import re
from typing import Dict, List, Optional, Any, Union, Callable
from pydantic import BaseModel, Field, validator, root_validator, constr, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from passlib.context import CryptContext



# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/api_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("strategy-api")

# ===== USER MANAGEMENT MODELS =====

class UserBase(BaseModel):
    """Base user model"""
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False
    
class UserCreate(UserBase):
    """User creation model"""
    password: constr(min_length=8)
    
class User(UserBase):
    """User model for database"""
    id: str
    hashed_password: str
    mfa_secret: Optional[str] = None
    mfa_enabled: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        
class UserResponse(UserBase):
    """User model for API responses"""
    id: str
    mfa_enabled: bool
    created_at: datetime
    
    class Config:
        orm_mode = True
        
class Token(BaseModel):
    """Token model for authentication responses"""
    access_token: str
    token_type: str
    user: UserResponse
    
class TokenData(BaseModel):
    """Token data model for JWT payload"""
    username: str
    user_id: str
    is_admin: bool = False
    exp: int

class MFASetup(BaseModel):
    """MFA setup model"""
    secret: str
    qr_code_url: str

class MFAVerify(BaseModel):
    """MFA verification model"""
    code: constr(min_length=6, max_length=6)

# ===== GUARDRAIL 2: RATE LIMITING =====

class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self, rate_limit: int, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            rate_limit: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.request_logs = defaultdict(lambda: deque(maxlen=rate_limit))
    
    def is_rate_limited(self, client_identifier: str) -> bool:
        """
        Check if client should be rate limited
        
        Args:
            client_identifier: Unique client identifier (e.g., IP address)
            
        Returns:
            bool: True if client should be rate limited, False otherwise
        """
        # Get client's request log
        client_requests = self.request_logs[client_identifier]
        
        # Get current time
        current_time = time.time()
        
        # Remove requests older than time window
        while client_requests and client_requests[0] < current_time - self.time_window:
            client_requests.popleft()
        
        # Check if client has reached rate limit
        if len(client_requests) >= self.rate_limit:
            return True
        
        # Add current request to log
        client_requests.append(current_time)
        return False

# ===== GUARDRAIL 3: DATA INTEGRITY =====

class DataValidator:
    """Data validation and sanitization"""
    
    @staticmethod
    def validate_summary_data(data_path: str) -> bool:
        """
        Validate summary report data
        
        Args:
            data_path: Path to summary report CSV file
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(data_path):
                logger.error(f"Summary data file not found: {data_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(data_path)
            if file_size == 0:
                logger.error(f"Summary data file is empty: {data_path}")
                return False
            
            # Check file age
            file_age = time.time() - os.path.getmtime(data_path)
            if file_age > 24 * 60 * 60:  # 24 hours
                logger.warning(f"Summary data file is older than 24 hours: {data_path}")
                # Continue validation, just a warning
            
            # Check file content
            df = pd.read_csv(data_path)
            
            # Check required columns
            required_columns = ['strategy', 'market_type', 'total_return', 'win_rate', 'sharpe_ratio']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Summary data file missing required columns: {missing_columns}")
                return False
            
            # Check for duplicate entries
            if df.duplicated(['strategy', 'market_type']).any():
                logger.warning(f"Summary data file contains duplicate entries")
                # Continue validation, just a warning
            
            # Check for valid values
            if df['total_return'].isnull().all() or df['win_rate'].isnull().all():
                logger.error(f"Summary data contains no valid metrics")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating summary data: {str(e)}")
            return False
    
    @staticmethod
    def validate_weights_data(data_path: str) -> bool:
        """
        Validate weights data
        
        Args:
            data_path: Path to weight table JSON file
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(data_path):
                logger.error(f"Weights data file not found: {data_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(data_path)
            if file_size == 0:
                logger.error(f"Weights data file is empty: {data_path}")
                return False
            
            # Check file age
            file_age = time.time() - os.path.getmtime(data_path)
            if file_age > 24 * 60 * 60:  # 24 hours
                logger.warning(f"Weights data file is older than 24 hours: {data_path}")
                # Continue validation, just a warning
            
            # Check file content
            with open(data_path, 'r') as f:
                weights = json.load(f)
            
            # Check if weights is a dictionary
            if not isinstance(weights, dict):
                logger.error(f"Weights data is not a dictionary")
                return False
            
            # Check if weights are empty
            if not weights:
                logger.error(f"Weights data is empty")
                return False
            
            # Check weight format for each market type
            strategies = ['Arbitrage', 'DCA', 'GridTrading', 'MeanReversion', 'Scalping', 'TrendFollowing']
            for market_type, market_weights in weights.items():
                # Check if market weights is a dictionary
                if not isinstance(market_weights, dict):
                    logger.error(f"Weights for market type {market_type} is not a dictionary")
                    return False
                
                # Check if all strategies are present
                missing_strategies = [s for s in strategies if s not in market_weights]
                if missing_strategies:
                    logger.error(f"Weights for market type {market_type} missing strategies: {missing_strategies}")
                    return False
                
                # Check if all weights are valid
                for strategy, weight in market_weights.items():
                    if not isinstance(weight, (int, float)):
                        logger.error(f"Weight for {strategy} in {market_type} is not a number: {weight}")
                        return False
                    if weight < 0.0 or weight > 1.0:
                        logger.error(f"Weight for {strategy} in {market_type} is out of range: {weight}")
                        return False
                
                # Check if weights sum to approximately 1.0 (allowing for floating point imprecision)
                weight_sum = sum(market_weights.values())
                if not (0.98 <= weight_sum <= 1.02):  # Allow small margin of error for floating point
                    logger.warning(f"Weights for market type {market_type} do not sum to 1.0: {weight_sum}")
                    # Continue validation, just a warning
            
            return True
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in weights file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error validating weights data: {str(e)}")
            return False

# ===== GUARDRAIL 4: SECURITY AUTHENTICATION =====

class SecurityGuard:
    """Security guardrails including API key validation"""
    
    def __init__(self, api_key_enabled: bool = False):
        """Initialize security guard with optional API key validation"""
        self.api_key_enabled = api_key_enabled
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        
        # In a real system, API keys would be stored in a secure database
        # For this example, we'll use environment variables or hardcoded for demonstration
        self.valid_api_keys = {
            os.environ.get("API_KEY", "topsecret-apikey-for-demo"): {
                "client": "admin",
                "rate_limit": 100
            }
        }
    
    async def get_api_key(self, api_key_header: str = Security(APIKeyHeader(name="X-API-Key", auto_error=False))):
        """
        Validate API key from header
        
        Args:
            api_key_header: API key from X-API-Key header
            
        Returns:
            dict: Client info if API key is valid
            
        Raises:
            HTTPException: If API key is invalid or missing
        """
        if not self.api_key_enabled:
            # If API key validation is disabled, return default client
            return {"client": "default", "rate_limit": 60}
        
        if api_key_header is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is required",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        if api_key_header not in self.valid_api_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        return self.valid_api_keys[api_key_header]

# ===== USER MANAGEMENT AND AUTHENTICATION =====

class UserManager:
    """User management functionality"""
    
    def __init__(self):
        """Initialize UserManager"""
        # In a real system, users would be stored in a database
        # For this example, we'll use an in-memory dictionary
        self.users = {}
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/token")
        
        # JWT configuration
        self.SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_hex(32))
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        # Create a default admin user if none exists
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create a default admin user if none exists"""
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "P@ssw0rd!")
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
        
        # Check if admin user already exists
        if not self.get_user_by_username(admin_username):
            # Create admin user
            admin_id = secrets.token_hex(16)
            self.users[admin_id] = {
                "id": admin_id,
                "username": admin_username,
                "email": admin_email,
                "hashed_password": self.get_password_hash(admin_password),
                "is_active": True,
                "is_admin": True,
                "mfa_secret": None,
                "mfa_enabled": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            logger.info(f"Created default admin user: {admin_username}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username: User's username
            
        Returns:
            User data if found, None otherwise
        """
        for user_id, user in self.users.items():
            if user["username"] == username:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User's ID
            
        Returns:
            User data if found, None otherwise
        """
        return self.users.get(user_id)
    
    def create_user(self, user: UserCreate) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            user: User creation data
            
        Returns:
            Created user data
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username already exists
        if self.get_user_by_username(user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Generate user ID
        user_id = secrets.token_hex(16)
        
        # Create user
        self.users[user_id] = {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "hashed_password": self.get_password_hash(user.password),
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "mfa_secret": None,
            "mfa_enabled": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        logger.info(f"Created user: {user.username}")
        return self.users[user_id]
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User data if authentication successful, None otherwise
        """
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        if not user["is_active"]:
            return None
        return user
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password is correct, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Token payload data
            expires_delta: Optional expiration timedelta
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="v1/auth/token"))) -> Dict[str, Any]:
        """
        Get current user from token
        
        Args:
            token: JWT token
            
        Returns:
            User data
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: str = payload.get("username")
            user_id: str = payload.get("user_id")
            if username is None or user_id is None:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception
        
        user = self.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        return user
    
    async def get_current_active_user(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """
        Get current active user
        
        Args:
            current_user: Current user data
            
        Returns:
            User data
            
        Raises:
            HTTPException: If user is not active
        """
        if not current_user["is_active"]:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    async def get_current_admin_user(self, current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
        """
        Get current admin user
        
        Args:
            current_user: Current user data
            
        Returns:
            User data
            
        Raises:
            HTTPException: If user is not an admin
        """
        if not current_user["is_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        return current_user
    
    def setup_mfa(self, user_id: str) -> MFASetup:
        """
        Setup MFA for a user
        
        Args:
            user_id: User's ID
            
        Returns:
            MFA setup data
            
        Raises:
            HTTPException: If user not found or MFA already enabled
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user["mfa_enabled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA already enabled"
            )
        
        # Generate MFA secret
        secret = pyotp.random_base32()
        
        # Save MFA secret to user
        user["mfa_secret"] = secret
        user["updated_at"] = datetime.now()
        self.users[user_id] = user
        
        # Generate QR code URL
        totp = pyotp.TOTP(secret)
        qr_code_url = totp.provisioning_uri(name=user["email"], issuer_name="Strategy API")
        
        return MFASetup(secret=secret, qr_code_url=qr_code_url)
    
    def verify_mfa(self, user_id: str, code: str) -> bool:
        """
        Verify MFA code
        
        Args:
            user_id: User's ID
            code: MFA code
            
        Returns:
            True if code is valid, False otherwise
            
        Raises:
            HTTPException: If user not found or MFA not set up
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user["mfa_secret"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA not set up"
            )
        
        # Verify code
        totp = pyotp.TOTP(user["mfa_secret"])
        return totp.verify(code)
    
    def enable_mfa(self, user_id: str, code: str) -> bool:
        """
        Enable MFA for a user
        
        Args:
            user_id: User's ID
            code: MFA code
            
        Returns:
            True if MFA was enabled, False otherwise
            
        Raises:
            HTTPException: If user not found, MFA not set up, or code is invalid
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user["mfa_secret"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA not set up"
            )
        
        if user["mfa_enabled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA already enabled"
            )
        
        # Verify code
        if not self.verify_mfa(user_id, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
        
        # Enable MFA
        user["mfa_enabled"] = True
        user["updated_at"] = datetime.now()
        self.users[user_id] = user
        
        return True
    
    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for a user
        
        Args:
            user_id: User's ID
            
        Returns:
            True if MFA was disabled, False otherwise
            
        Raises:
            HTTPException: If user not found or MFA not enabled
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user["mfa_enabled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA not enabled"
            )
        
        # Disable MFA
        user["mfa_enabled"] = False
        user["mfa_secret"] = None
        user["updated_at"] = datetime.now()
        self.users[user_id] = user
        
        return True


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/api_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("strategy-api")

# Models for API validation
class StrategyMetrics(BaseModel):
    strategy: constr(min_length=1, max_length=100)
    market_type: constr(min_length=1, max_length=100)
    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown_pct: Optional[float] = None
    
    @validator('total_return', 'win_rate', 'sharpe_ratio', 'max_drawdown_pct', pre=True)
    def validate_numeric(cls, v):
        """Validate numeric fields are within reasonable bounds"""
        if v is None:
            return None
        if isinstance(v, str):
            if v.lower() in ('inf', '+inf', 'infinity', '+infinity'):
                return float('inf')
            elif v.lower() in ('-inf', '-infinity'):
                return float('-inf')
            try:
                v = float(v)
            except ValueError:
                raise ValueError(f"Cannot convert {v} to a number")
        
        # Check for NaN
        if isinstance(v, float) and pd.isna(v):
            return None
            
        return v

class WeightEntry(BaseModel):
    Arbitrage: float = Field(..., ge=0.0, le=1.0)
    DCA: float = Field(..., ge=0.0, le=1.0)
    GridTrading: float = Field(..., ge=0.0, le=1.0)
    MeanReversion: float = Field(..., ge=0.0, le=1.0)
    Scalping: float = Field(..., ge=0.0, le=1.0)
    TrendFollowing: float = Field(..., ge=0.0, le=1.0)
    
    @validator('Arbitrage', 'DCA', 'GridTrading', 'MeanReversion', 'Scalping', 'TrendFollowing')
    def validate_weight(cls, v):
        """Validate weights are between 0 and 1"""
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Weight value {v} must be between 0 and 1")
        return v

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    timestamp: str
    guardrails: Optional[Dict[str, bool]] = None

# Get the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Rate limiter implementation
class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self, rate_limit: int, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            rate_limit: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.request_logs = defaultdict(lambda: deque(maxlen=rate_limit))
    
    def is_rate_limited(self, client_identifier: str) -> bool:
        """
        Check if client should be rate limited
        
        Args:
            client_identifier: Unique client identifier (e.g., IP address)
            
        Returns:
            bool: True if client should be rate limited, False otherwise
        """
        # Get client's request log
        client_requests = self.request_logs[client_identifier]
        
        # Get current time
        current_time = time.time()
        
        # Remove requests older than time window
        while client_requests and client_requests[0] < current_time - self.time_window:
            client_requests.popleft()
        
        # Check if client has reached rate limit
        if len(client_requests) >= self.rate_limit:
            return True
        
        # Add current request to log
        client_requests.append(current_time)
        return False

# Configuration
class Settings:
    def __init__(self):
        self.app_name = "Strategy Analysis API"
        self.version = "2.0.0"
        self.start_time = time.time()
        self.data_dir = os.path.join(PROJECT_ROOT, "data")
        self.debug = os.environ.get("DEBUG", "false").lower() == "true"
        self.enable_api_key = os.environ.get("ENABLE_API_KEY", "false").lower() == "true"
        self.rate_limit = int(os.environ.get("RATE_LIMIT", "60"))
        self.require_data_validation = os.environ.get("REQUIRE_DATA_VALIDATION", "true").lower() == "true"

# Initialize settings
settings = Settings()

# Data Validation class
class DataValidator:
    """Data validation and sanitization"""
    
    @staticmethod
    def validate_summary_data(data_path: str) -> bool:
        """
        Validate summary report data
        
        Args:
            data_path: Path to summary report CSV file
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(data_path):
                logger.error(f"Summary data file not found: {data_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(data_path)
            if file_size == 0:
                logger.error(f"Summary data file is empty: {data_path}")
                return False
            
            # Check file content
            df = pd.read_csv(data_path)
            
            # Check required columns
            required_columns = ['strategy', 'market_type', 'total_return', 'win_rate', 'sharpe_ratio']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Summary data file missing required columns: {missing_columns}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating summary data: {str(e)}")
            return False
    
    @staticmethod
    def validate_weights_data(data_path: str) -> bool:
        """
        Validate weights data
        
        Args:
            data_path: Path to weight table JSON file
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(data_path):
                logger.error(f"Weights data file not found: {data_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(data_path)
            if file_size == 0:
                logger.error(f"Weights data file is empty: {data_path}")
                return False
            
            # Check file content
            with open(data_path, 'r') as f:
                weights = json.load(f)
            
            # Check if weights is a dictionary
            if not isinstance(weights, dict):
                logger.error(f"Weights data is not a dictionary")
                return False
            
            return True
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in weights file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error validating weights data: {str(e)}")
            return False

# Security guard for API key authentication
class SecurityGuard:
    """Security guardrails including API key validation"""
    
    def __init__(self, api_key_enabled: bool = False):
        """Initialize security guard with optional API key validation"""
        self.api_key_enabled = api_key_enabled
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        
        # In a real system, API keys would be stored in a secure database
        # For this example, we'll use environment variables or hardcoded for demonstration
        self.valid_api_keys = {
            os.environ.get("API_KEY", "topsecret-apikey-for-demo"): {
                "client": "admin",
                "rate_limit": 100
            }
        }
    
    async def get_api_key(self, api_key_header: str = Security(APIKeyHeader(name="X-API-Key", auto_error=False))):
        """
        Validate API key from header
        
        Args:
            api_key_header: API key from X-API-Key header
            
        Returns:
            dict: Client info if API key is valid
            
        Raises:
            HTTPException: If API key is invalid or missing
        """
        if not self.api_key_enabled:
            # If API key validation is disabled, return default client
            return {"client": "default", "rate_limit": 60}
        
        if api_key_header is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is required",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        if api_key_header not in self.valid_api_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        return self.valid_api_keys[api_key_header]

# Initialize components
settings = Settings()
data_validator = DataValidator()
security_guard = SecurityGuard(api_key_enabled=settings.enable_api_key)

# Create the FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production API for strategy backtesting analysis and weights",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, use specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.4f}s"
    )
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Generate a unique error ID for tracking
    error_id = secrets.token_hex(8)
    
    logger.error(f"Unhandled exception: {str(exc)} (Error ID: {error_id})", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred.",
            "errorId": error_id,
            "timestamp": datetime.now().isoformat()
        }
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    # Check data file validity
    summary_path = os.path.join(settings.data_dir, "summary_report.csv")
    weights_path = os.path.join(settings.data_dir, "weight_table.json")
    
    summary_valid = data_validator.validate_summary_data(summary_path)
    weights_valid = data_validator.validate_weights_data(weights_path)
    
    return {
        "status": "healthy" if (summary_valid and weights_valid) else "degraded",
        "version": settings.version,
        "uptime": time.time() - settings.start_time,
        "timestamp": datetime.now().isoformat(),
        "guardrails": {
            "api_key_auth": settings.enable_api_key,
            "data_validation": settings.require_data_validation,
            "summary_data_valid": summary_valid,
            "weights_data_valid": weights_valid,
            "security_headers": True,
            "error_tracking": True
        }
    }

# ===== USER AUTHENTICATION ROUTES =====

@app.post("/v1/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    try:
        # Create user
        created_user = user_manager.create_user(user)
        
        # Log audit event
        audit_logger.log_security_event(
            event_type="USER_REGISTERED",
            details=f"User {user.username} registered",
            severity="INFO"
        )
        
        # Return user response
        return user_manager.user_to_response(created_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )

@app.post("/v1/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), mfa_code: Optional[str] = Form(None)):
    """
    OAuth2 compatible token login, get an access token for future requests
    
    Args:
        form_data: OAuth2 password request form
        mfa_code: Optional MFA code for 2FA
        
    Returns:
        Access token and user data
    """
    # Authenticate user
    user = user_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        # Log failed login attempt
        audit_logger.log_security_event(
            event_type="LOGIN_FAILED",
            details=f"Failed login attempt for user {form_data.username}",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if MFA is enabled
    if user["mfa_enabled"]:
        if not mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA code required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify MFA code
        if not user_manager.verify_mfa(user["id"], mfa_code):
            # Log failed MFA attempt
            audit_logger.log_security_event(
                event_type="MFA_FAILED",
                details=f"Failed MFA attempt for user {user['username']}",
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Create access token
    access_token_expires = timedelta(minutes=user_manager.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_manager.create_access_token(
        data={
            "username": user["username"],
            "user_id": user["id"],
            "is_admin": user["is_admin"]
        },
        expires_delta=access_token_expires
    )
    
    # Log successful login
    audit_logger.log_security_event(
        event_type="LOGIN_SUCCESS",
        details=f"User {user['username']} logged in",
        severity="INFO"
    )
    
    # Return token and user data
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_manager.user_to_response(user)
    }

@app.get("/v1/auth/me", response_model=UserResponse)
async def read_users_me(current_user: Dict[str, Any] = Depends(user_manager.get_current_active_user)):
    """Get information about the current user"""
    return user_manager.user_to_response(current_user)

@app.post("/v1/auth/mfa/setup", response_model=MFASetup)
async def setup_mfa(current_user: Dict[str, Any] = Depends(user_manager.get_current_active_user)):
    """Setup MFA for the current user"""
    # Setup MFA
    mfa_setup = user_manager.setup_mfa(current_user["id"])
    
    # Log MFA setup
    audit_logger.log_security_event(
        event_type="MFA_SETUP",
        details=f"User {current_user['username']} set up MFA",
        severity="INFO"
    )
    
    return mfa_setup

@app.post("/v1/auth/mfa/enable")
async def enable_mfa(
    mfa_verify: MFAVerify,
    current_user: Dict[str, Any] = Depends(user_manager.get_current_active_user)
):
    """Enable MFA for the current user"""
    # Enable MFA
    user_manager.enable_mfa(current_user["id"], mfa_verify.code)
    
    # Log MFA enabled
    audit_logger.log_security_event(
        event_type="MFA_ENABLED",
        details=f"User {current_user['username']} enabled MFA",
        severity="INFO"
    )
    
    return {"status": "success", "message": "MFA enabled"}

@app.post("/v1/auth/mfa/disable")
async def disable_mfa(current_user: Dict[str, Any] = Depends(user_manager.get_current_active_user)):
    """Disable MFA for the current user"""
    # Disable MFA
    user_manager.disable_mfa(current_user["id"])
    
    # Log MFA disabled
    audit_logger.log_security_event(
        event_type="MFA_DISABLED",
        details=f"User {current_user['username']} disabled MFA",
        severity="INFO"
    )
    
    return {"status": "success", "message": "MFA disabled"}

# ===== ADMIN ROUTES =====

@app.get("/v1/admin/users", response_model=List[UserResponse])
async def get_all_users(admin_user: Dict[str, Any] = Depends(user_manager.get_current_admin_user)):
    """Get all users (admin only)"""
    # Get all users
    users = list(user_manager.users.values())
    
    # Log admin action
    audit_logger.log_security_event(
        event_type="ADMIN_GET_USERS",
        details=f"Admin {admin_user['username']} retrieved all users",
        severity="INFO"
    )
    
    # Convert to UserResponse models
    return [user_manager.user_to_response(user) for user in users]

@app.get("/v1/admin/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(user_manager.get_current_admin_user)
):
    """Get a specific user (admin only)"""
    # Get user
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin action
    audit_logger.log_security_event(
        event_type="ADMIN_GET_USER",
        details=f"Admin {admin_user['username']} retrieved user {user['username']}",
        severity="INFO"
    )
    
    # Return user response
    return user_manager.user_to_response(user)

@app.put("/v1/admin/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(user_manager.get_current_admin_user)
):
    """Activate a user (admin only)"""
    # Get user
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Activate user
    user["is_active"] = True
    user["updated_at"] = datetime.now()
    user_manager.users[user_id] = user
    
    # Log admin action
    audit_logger.log_security_event(
        event_type="ADMIN_ACTIVATE_USER",
        details=f"Admin {admin_user['username']} activated user {user['username']}",
        severity="INFO"
    )
    
    return {"status": "success", "message": "User activated"}

@app.put("/v1/admin/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(user_manager.get_current_admin_user)
):
    """Deactivate a user (admin only)"""
    # Get user
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating self
    if user_id == admin_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    # Deactivate user
    user["is_active"] = False
    user["updated_at"] = datetime.now()
    user_manager.users[user_id] = user
    
    # Log admin action
    audit_logger.log_security_event(
        event_type="ADMIN_DEACTIVATE_USER",
        details=f"Admin {admin_user['username']} deactivated user {user['username']}",
        severity="INFO"
    )
    
    return {"status": "success", "message": "User deactivated"}

# Define routes
@app.get("/v1/analysis/summary", response_model=List[StrategyMetrics])
async def get_summary(client: Dict[str, Any] = Depends(security_guard.get_api_key)):
    """Get strategy summary report data"""
    try:
        csv_path = os.path.join(settings.data_dir, "summary_report.csv")
        if not os.path.exists(csv_path):
            logger.error(f"Summary data file not found at {csv_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Summary data not found"
            )
        
        # Validate data if required
        if settings.require_data_validation:
            if not data_validator.validate_summary_data(csv_path):
                logger.error(f"Summary data validation failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Summary data validation failed"
                )
        
        # Read CSV with explicit handling of missing values
        logger.info(f"Loading summary data from {csv_path}")
        df = pd.read_csv(csv_path)
        
        # Convert to records, handling special values
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val) or pd.isnull(val):
                    record[col] = None
                elif isinstance(val, float) and (val == float('inf') or val == float('-inf')):
                    record[col] = str(val)  # Convert inf/-inf to strings
                else:
                    record[col] = val
            records.append(record)
            
        logger.info(f"Processed {len(records)} summary records successfully")
        return records
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to process summary data: {str(e)}"
        )

@app.get("/v1/analysis/weights", response_model=Dict[str, WeightEntry])
async def get_weights(client: Dict[str, Any] = Depends(security_guard.get_api_key)):
    """Get strategy weights data"""
    try:
        json_path = os.path.join(settings.data_dir, "weight_table.json")
        if not os.path.exists(json_path):
            logger.error(f"Weights data file not found at {json_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Weights data not found"
            )
        
        # Validate data if required
        if settings.require_data_validation:
            if not data_validator.validate_weights_data(json_path):
                logger.error(f"Weights data validation failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Weights data validation failed"
                )
        
        logger.info(f"Loading weights data from {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                weights = json.load(f)
                logger.info(f"Loaded weights for {len(weights)} market types")
                return weights
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {str(je)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail=f"Invalid JSON in weights file: {str(je)}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_weights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to process weights data: {str(e)}"
        )

# Metadata endpoint for discoverability
@app.get("/v1/analysis/metadata")
async def get_metadata(client: Dict[str, Any] = Depends(security_guard.get_api_key)):
    """Get metadata about available analysis endpoints"""
    return {
        "endpoints": [
            {
                "path": "/v1/analysis/summary",
                "description": "Strategy summary statistics",
                "method": "GET"
            },
            {
                "path": "/v1/analysis/weights",
                "description": "Strategy weights per market type",
                "method": "GET"
            }
        ],
        "version": settings.version,
        "guardrails": {
            "api_key_auth": settings.enable_api_key,
            "data_validation": settings.require_data_validation,
            "security_headers": True,
            "error_tracking": True
        }
    }

# ===== STARTUP AND SHUTDOWN EVENTS =====

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    # Log startup
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    
    # Check data files
    summary_path = os.path.join(settings.data_dir, "summary_report.csv")
    weights_path = os.path.join(settings.data_dir, "weight_table.json")
    
    # Log validation results
    summary_valid = data_validator.validate_summary_data(summary_path)
    weights_valid = data_validator.validate_weights_data(weights_path)
    
    logger.info(f"Data validation: Summary={summary_valid}, Weights={weights_valid}")
    
    # Log security configuration
    logger.info(f"Security: API Key Auth={settings.enable_api_key}, Rate Limit={settings.rate_limit}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    # Log shutdown
    logger.info(f"Shutting down {settings.app_name} v{settings.version}")
    logger.info(f"API uptime: {time.time() - settings.start_time:.2f}s")

# Run the server when this script is executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting {settings.app_name} v{settings.version} on {host}:{port}")
    logger.info(f"API URLs:")
    logger.info(f"  - http://localhost:{port}/v1/analysis/summary")
    logger.info(f"  - http://localhost:{port}/v1/analysis/weights")
    logger.info(f"  - http://localhost:{port}/health (health check)")
    logger.info(f"  - http://localhost:{port}/docs (API documentation)")
    
    # Use reload only in development
    uvicorn.run(
        "production_api_server:app", 
        host=host, 
        port=port, 
        reload=settings.debug,
        log_level="info"
    )
