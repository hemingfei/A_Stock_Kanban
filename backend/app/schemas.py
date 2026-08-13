from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# === Base Schemas ===

class ApiResponse(BaseModel):
    """Standard API response format."""
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class ApiError(BaseModel):
    """API error format."""
    code: str
    message: str
    details: Optional[List[Dict[str, Any]]] = None
    request_id: Optional[str] = None


# === User/Auth Schemas ===

class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=2, max_length=50)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


# === Board Schemas ===

class BoardBase(BaseModel):
    """Base board schema."""
    name: str = Field(..., min_length=1, max_length=100)


class BoardCreate(BoardBase):
    """Schema for creating a board."""
    pass


class BoardUpdate(BoardBase):
    """Schema for updating a board."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    sort_order: Optional[int] = None


class BoardResponse(BoardBase):
    """Schema for board response."""
    id: int
    user_id: int
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BoardWithStocks(BoardResponse):
    """Board with stocks included."""
    stocks: List["StockResponse"] = []


# === Stock Schemas ===

class StockBase(BaseModel):
    """Base stock schema."""
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=50)


class StockCreate(StockBase):
    """Schema for adding a stock to a board."""
    pass


class StockUpdate(BaseModel):
    """Schema for updating a stock."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    sort_order: Optional[int] = None


class StockResponse(StockBase):
    """Schema for stock response."""
    id: int
    board_id: int
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


# === Quote Schemas ===

class Quote(BaseModel):
    """Stock quote schema."""
    code: str
    name: str
    price: float
    pre_close: float
    open: float
    high: float
    low: float
    volume: float
    amount: float
    change: float
    change_percent: float
    bid1: Optional[float] = None
    bid1_volume: Optional[float] = None
    ask1: Optional[float] = None
    ask1_volume: Optional[float] = None
    timestamp: float
    stale: bool = False


class QuoteRequest(BaseModel):
    """Request schema for quotes."""
    codes: List[str]


# === K-Line Schemas ===

class KLineItem(BaseModel):
    """K-line data item."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    change: float
    change_percent: float


class KLinePeriod(str):
    """K-line period options."""
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"
    MIN5 = "5m"
    MIN15 = "15m"
    MIN30 = "30m"
    MIN60 = "60m"


# === User Settings Schemas ===

class UserSettingBase(BaseModel):
    """Base user settings schema."""
    refresh_interval: int = Field(5, ge=1, le=60)
    data_sources: str = '["akshare"]'
    theme: str = Field("light", pattern="^(light|dark)$")


class UserSettingUpdate(BaseModel):
    """Schema for updating user settings."""
    refresh_interval: Optional[int] = Field(None, ge=1, le=60)
    data_sources: Optional[str] = None
    theme: Optional[str] = Field(None, pattern="^(light|dark)$")


class UserSettingResponse(UserSettingBase):
    """Schema for user settings response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# === Health Check Schemas ===

class HealthStatus(BaseModel):
    """Health check response."""
    status: str
    database: str
    redis: str
    datasource: str
    timestamp: str
    uptime: float


class ReadinessStatus(BaseModel):
    """Readiness check response."""
    status: str
    checks: Dict[str, str]
    timestamp: str


# === Audit Log Schemas ===

class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    id: int
    user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    ip_address: Optional[str]
    extra_data: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# === WebSocket Schemas ===

class WSMessage(BaseModel):
    """WebSocket message base schema."""
    type: str


class WSSubscribe(WSMessage):
    """WebSocket subscribe message."""
    type: str = "subscribe"
    codes: List[str]


class WSUnsubscribe(WSMessage):
    """WebSocket unsubscribe message."""
    type: str = "unsubscribe"
    codes: List[str]


class WSPong(WSMessage):
    """WebSocket pong response."""
    type: str = "pong"


class WSQuoteUpdate(WSMessage):
    """WebSocket quote update message."""
    type: str = "quote"
    data: Quote


class WSQuotesUpdate(WSMessage):
    """WebSocket batch quotes update message."""
    type: str = "quotes"
    data: Dict[str, Any]


class WSError(WSMessage):
    """WebSocket error message."""
    type: str = "error"
    code: str
    message: str


# === Reorder Schemas ===

class BoardReorderRequest(BaseModel):
    """Request for reordering boards."""
    board_ids: List[int]


class StockReorderRequest(BaseModel):
    """Request for reordering stocks in a board."""
    stock_ids: List[int]


# Update forward references
BoardWithStocks.model_rebuild()
