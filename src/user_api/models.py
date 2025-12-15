from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class User(BaseModel):
    """User model for API responses."""
    uuid: UUID = Field(..., description="User's unique identifier")
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            }
        }


class UserInternal(BaseModel):
    """Internal user model with ID (used in DAL, not exposed via API)."""
    id: int
    uuid: UUID
    first_name: str
    last_name: str
    email: EmailStr
