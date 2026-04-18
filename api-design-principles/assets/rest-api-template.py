"""
Production-ready REST API template using FastAPI.

Includes:
- Bearer-token authentication (dependency-injected)
- Generic paginated response type
- Request-ID middleware + structured logging
- Consistent error envelope
- Typed CRUD endpoints with filtering + pagination
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from enum import Enum
from typing import Generic, List, Optional, TypeVar

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Structured logging with request-ID propagation
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","request_id":"%(request_id)s","msg":"%(message)s"}'
    )
)
handler.addFilter(RequestIdFilter())
logger.addHandler(handler)

app = FastAPI(title="API Template", version="1.0.0", docs_url="/api/docs")

# Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # TODO: restrict in production, e.g. ["api.example.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: set explicit origins in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request_id_ctx.set(request_id)
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


# Authentication
bearer = HTTPBearer(auto_error=False)


async def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> dict:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    # TODO: verify JWT / lookup API key. Stub for template:
    if creds.credentials != os.environ.get("DEV_TOKEN", "dev-token"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return {"sub": "user_123", "role": "admin", "scope": "users:read users:write"}


def require_scope(scope: str):
    async def checker(user: dict = Depends(current_user)) -> dict:
        if scope not in user.get("scope", "").split():
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Missing required scope: {scope}"
            )
        return user

    return checker


# Models
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    status: UserStatus = UserStatus.ACTIVE


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[UserStatus] = None


class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Generic pagination
T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: List[T], total: int, params: PaginationParams) -> "Page[T]":
        pages = (total + params.page_size - 1) // params.page_size if total else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )


async def paginate_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


# Error envelope
class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    code: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: str


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else detail.get("message", "Error")
    details = detail.get("details") if isinstance(detail, dict) else None
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=message,
            details=details,
            request_id=request_id_ctx.get(),
        ).model_dump(),
        headers={"X-Request-ID": request_id_ctx.get()},
    )


# Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": app.version}


@app.get("/api/users", response_model=Page[User], tags=["Users"])
async def list_users(
    params: PaginationParams = Depends(paginate_params),
    status_filter: Optional[UserStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    _auth: dict = Depends(require_scope("users:read")),  # auth side-effect
):
    """List users with pagination and filtering."""
    # Mock data source — replace with DB query in production
    all_users = [
        User(
            id=str(i),
            email=f"user{i}@example.com",
            name=f"User {i}",
            status=UserStatus.ACTIVE if i % 3 else UserStatus.INACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(100)
    ]

    # Apply filters over the full set before paginating
    filtered = [
        u
        for u in all_users
        if (status_filter is None or u.status == status_filter)
        and (search is None or search.lower() in u.name.lower())
    ]

    total = len(filtered)
    start = (params.page - 1) * params.page_size
    items = filtered[start : start + params.page_size]
    return Page.build(items=items, total=total, params=params)


@app.post(
    "/api/users",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
async def create_user(
    payload: UserCreate,
    _auth: dict = Depends(require_scope("users:write")),  # auth side-effect
):
    """Create a new user."""
    now = datetime.now(timezone.utc)
    return User(
        id=str(uuid.uuid4()),
        email=payload.email,
        name=payload.name,
        status=payload.status,
        created_at=now,
        updated_at=now,
    )


async def _fetch_user(user_id: str) -> User:
    """Internal helper — replace with repository call."""
    if user_id == "999":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "details": {"id": user_id}},
        )
    return User(
        id=user_id,
        email="user@example.com",
        name="User Name",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@app.get("/api/users/{user_id}", response_model=User, tags=["Users"])
async def get_user(
    user_id: str = Path(..., description="User ID"),
    _auth: dict = Depends(require_scope("users:read")),  # auth side-effect
):
    """Get user by ID."""
    return await _fetch_user(user_id)


@app.patch("/api/users/{user_id}", response_model=User, tags=["Users"])
async def update_user(
    user_id: str,
    update: UserUpdate,
    _auth: dict = Depends(require_scope("users:write")),  # auth side-effect
):
    """Partially update a user."""
    existing = await _fetch_user(user_id)
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(existing, field, value)
    existing.updated_at = datetime.now(timezone.utc)
    return existing


@app.delete(
    "/api/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Users"],
)
async def delete_user(
    user_id: str,
    _auth: dict = Depends(require_scope("users:write")),  # auth side-effect
):
    """Delete a user."""
    await _fetch_user(user_id)
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
