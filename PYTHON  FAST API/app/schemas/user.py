"""
User-related Pydantic schemas.
"""
import uuid
from pydantic import BaseModel, Field, EmailStr
from typing import Optional     


class UserCreate(BaseModel):
    """Schema for creating a new user (without user_id)"""
    user_name: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")

class User(UserCreate):
    """User model with auto-generated user_id"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[str] = None
    is_active: bool = Field(default=True, description="Whether the user account is active")


class UserResponse(BaseModel):
    """User response model (without password)"""
    user_id: str
    user_name: str
    email: EmailStr
    created_at: Optional[str] = None
    is_active: bool = True


class UserUpdate(BaseModel):
    """Schema for updating user (all fields optional)"""
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Valid email address")
    password: Optional[str] = Field(None, min_length=6, description="Password (minimum 6 characters)")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")


class LoginRequest(BaseModel):
    """Login model"""
    user_name: str 
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str 


class TokenResponse(BaseModel):
    """JWT token response model"""
    access_token: str
    refresh_token: Optional[str] = ""
    token_type: str = "bearer"

