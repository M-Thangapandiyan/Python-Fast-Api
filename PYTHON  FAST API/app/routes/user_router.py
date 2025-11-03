"""
User management routes.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
import uuid
from datetime import datetime
from app.schemas.user import User, UserCreate, UserResponse, UserUpdate
from app.core.config import settings
from app.core.security import hash_password
from app.db import database
from app.routes.document_router import get_current_user


router = APIRouter(
    prefix=settings.API_V1_PREFIX,
    tags=["users"],
)


@router.post("/user/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    """
    Create a new user with hashed password.
    
    Validates:
    - Username must be 3-50 characters
    - Email must be valid format
    - Password must be minimum 6 characters
    """
    try:

        existing_user = database.get_user(username=user.user_name)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        
        existing_email_user = database.get_user(email=user.email)
        if existing_email_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(user.password)

        create_at = datetime.now().isoformat()
        
        user_with_hash = User(
            user_id=str(uuid.uuid4()),
            user_name=user.user_name,
            email=user.email,
            password=hashed_password,
            created_at=create_at,
            is_active=True
        )
        
        database.create_user(user_with_hash)
        
        return UserResponse(
            user_id=user_with_hash.user_id,
            user_name=user_with_hash.user_name,
            email=user_with_hash.email,
            created_at=user_with_hash.created_at,
            is_active=user_with_hash.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    

@router.get("/user/", response_model=UserResponse)
def get_user_by_user_name_or_email(username: Optional[str] = Query(None), email: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    """
    Get user by username or email.
    """
    try:
        if username:
            user_data = database.get_user(username=username)
        elif email:
            user_data = database.get_user(email=email)
        else:
            raise HTTPException(status_code=400, detail="Either username or email must be provided")
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_data.get("user_id"),
            "user_name": user_data.get("user_name"),
            "email": user_data.get("email"),
            "created_at": user_data.get("created_at"),
            "is_active": user_data.get("is_active", True)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")
    
    
@router.get("/users/", response_model=List[UserResponse], status_code=200)    
def get_all_users(current_user: dict = Depends(get_current_user)):    
    """
    Get all users.
    Requires authentication.
    """
    try:
        users_data = database.get_all_user()
        
        users = []
        for user_data in users_data:
            users.append({
                "user_id": user_data.get("user_id"),
                "user_name": user_data.get("user_name"),
                "email": user_data.get("email"),
                "created_at": user_data.get("created_at"),
                "is_active": user_data.get("is_active", True)
            })
        
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")


@router.patch("/user/{username}", response_model=UserResponse, status_code=200)
def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user by username.
    Requires authentication.
    """
    try:
        existing_user = database.get_user(username=username)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = {}
        
        if user_update.email and user_update.email != existing_user.get("email"):
            email_user = database.get_user(email=user_update.email)
            if email_user and email_user.get("user_name") != username:
                raise HTTPException(status_code=400, detail="Email already registered")
            update_data["email"] = user_update.email

        if user_update.password:
            update_data["password"] = hash_password(user_update.password)

        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active
        
        # If no fields to update
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        
        # Update user in database
        updated_user = database.update_user(username=username, user_update=update_data)
        
        return {
            "user_id": updated_user.get("user_id"),
            "user_name": updated_user.get("user_name"),
            "email": updated_user.get("email"),
            "created_at": updated_user.get("created_at"),
            "is_active": updated_user.get("is_active", True)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/user/{username}", status_code=200)
def delete_user(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete user by username.
    Requires authentication.
    """
    try:
        # Check if user exists
        existing_user = database.get_user(username=username)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = database.delete_user(username=username)
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found or already deleted")
        
        return {"message": f"User '{username}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
         

