# FastAPI with automatic OpenAPI generation
# This example demonstrates code-first OpenAPI spec generation

from fastapi import FastAPI, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

app = FastAPI(
    title="User Management API",
    description="API for managing users and profiles",
    version="2.0.0",
    openapi_tags=[
        {"name": "Users", "description": "User operations"},
        {"name": "Profiles", "description": "Profile operations"},
    ],
    servers=[
        {"url": "https://api.example.com/v2", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Development"},
    ],
)


# Enums
class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending = "pending"


class UserRole(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


# Models
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")


class UserCreate(UserBase):
    role: UserRole = Field(default=UserRole.user)
    metadata: Optional[dict] = Field(default=None, description="Custom metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [{"email": "user@example.com", "name": "John Doe", "role": "user"}]
        }
    }


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None
    metadata: Optional[dict] = None


class User(UserBase):
    id: UUID = Field(..., description="Unique identifier")
    status: UserStatus
    role: UserRole
    avatar: Optional[str] = Field(None, description="Avatar URL")
    metadata: Optional[dict] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = {"populate_by_name": True}


class Pagination(BaseModel):
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0, alias="totalPages")
    has_next: bool = Field(..., alias="hasNext")
    has_prev: bool = Field(..., alias="hasPrev")


class UserListResponse(BaseModel):
    data: List[User]
    pagination: Pagination


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = Field(None, alias="requestId")


# Endpoints
@app.get(
    "/users",
    response_model=UserListResponse,
    tags=["Users"],
    summary="List all users",
    description="Returns a paginated list of users with optional filtering.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, min_length=2, max_length=100),
):
    """
    List users with pagination and filtering.

    - **page**: Page number (1-based)
    - **limit**: Number of items per page (max 100)
    - **status**: Filter by user status
    - **search**: Search by name or email
    """
    # Implementation
    pass


@app.post(
    "/users",
    response_model=User,
    status_code=201,
    tags=["Users"],
    summary="Create a new user",
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse, "description": "Email already exists"},
    },
)
async def create_user(user: UserCreate):
    """Create a new user and send welcome email."""
    pass


@app.get(
    "/users/{user_id}",
    response_model=User,
    tags=["Users"],
    summary="Get user by ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_user(
    user_id: UUID = Path(..., description="User ID"),
):
    """Retrieve a specific user by their ID."""
    pass


@app.patch(
    "/users/{user_id}",
    response_model=User,
    tags=["Users"],
    summary="Update user",
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def update_user(
    user_id: UUID = Path(..., description="User ID"),
    user: UserUpdate = ...,
):
    """Update user attributes."""
    pass


@app.delete(
    "/users/{user_id}",
    status_code=204,
    tags=["Users", "Admin"],
    summary="Delete user",
    responses={404: {"model": ErrorResponse}},
)
async def delete_user(
    user_id: UUID = Path(..., description="User ID"),
):
    """Permanently delete a user."""
    pass


# Export OpenAPI spec
if __name__ == "__main__":
    import json

    print(json.dumps(app.openapi(), indent=2))
