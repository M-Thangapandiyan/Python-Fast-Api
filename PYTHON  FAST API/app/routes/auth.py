"""
Authentication routes (login, token refresh).
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.user import LoginRequest, RefreshTokenRequest, TokenResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password
)
from app.db import database


router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login_user(login_request: LoginRequest):
    """
    Authenticate user with username and password.
    """
    try:
        # Get user from database
        user_data = database.get_user(username=login_request.user_name)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not verify_password(login_request.password, user_data.get("password")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        token_payload = {"sub": login_request.user_name}
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest):
    """
    Generate new access token using refresh token.
    """
    try:
        payload = verify_token(request.refresh_token, expected_type="refresh")

        # Extract username from token payload
        token_payload = {"sub": payload.get("sub")}
        access_token = create_access_token(token_payload)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )


