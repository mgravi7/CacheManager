from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID
from .models import User
from .dal import UserDAL
from cache_manager import CacheManager

router = APIRouter(prefix="/users", tags=["users"])


def get_user_dal() -> UserDAL:
    """Dependency injection for UserDAL."""
    cache_manager = CacheManager()
    return UserDAL(cache_manager)


@router.get("/", response_model=List[User], summary="Get all users")
async def get_all_users(dal: UserDAL = Depends(get_user_dal)) -> List[User]:
    """
    Retrieve all users.
    
    Returns a list of all users with their UUID, first name, last name, and email.
    """
    return await dal.get_all_users()


@router.get("/{user_uuid}", response_model=User, summary="Get user by UUID")
async def get_user_by_uuid(
    user_uuid: UUID,
    dal: UserDAL = Depends(get_user_dal)
) -> User:
    """
    Retrieve a specific user by UUID.
    
    This endpoint demonstrates cache usage:
    1. Check UUID->ID cache
    2. If cache hit, retrieve user data
    3. If cache miss, lookup user and populate cache
    
    Args:
        user_uuid: The UUID of the user to retrieve
        
    Returns:
        User object with UUID, first name, last name, and email
        
    Raises:
        HTTPException: 404 if user not found
    """
    user = await dal.get_user_by_uuid(user_uuid)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with UUID {user_uuid} not found"
        )
    
    return user
