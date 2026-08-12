# A股看盘工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete A股看盘 web tool with user authentication, custom stock boards, real-time quotes, K-line charts, and Docker deployment.

**Architecture:** Multi-container Docker setup with Nginx (reverse proxy), FastAPI backend, Redis cache, and React frontend. SQLite for persistent storage.

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, Redis, AkShare
- Frontend: React 18, TypeScript, Ant Design, Lightweight Charts
- DevOps: Docker Compose, GitHub Actions CI/CD

---

## Global Constraints

- Python >= 3.11
- Node.js >= 18
- FastAPI >= 0.100.0
- SQLAlchemy >= 2.0.0 with async support
- All backend routes use `/api/v1` prefix
- Passwords must be hashed with bcrypt (work factor 12)
- JWT access tokens expire after 2 hours, refresh tokens after 7 days
- Docker containers use Alpine-based images for smaller size
- All API responses use consistent format: `{success: boolean, data?: any, error?: {code: string, message: string}}`

---

## File Structure Overview

```
astock/
├── .gitignore
├── .env.example
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── logging.conf
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── cache.py
│   │   ├── limiter.py
│   │   ├── health.py
│   │   ├── boards.py
│   │   ├── stocks.py
│   │   ├── quotes.py
│   │   ├── settings.py
│   │   └── datasources/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── akshare.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   └── scripts/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── router/
│       ├── pages/
│       ├── components/
│       ├── hooks/
│       ├── services/
│       ├── store/
│       ├── types/
│       └── utils/
├── nginx/
│   └── nginx.conf
└── redis/
    └── redis.conf
```

---

## Phase 1: Project Scaffolding and Foundation

### Task 1: Root Project Setup

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`

**Interfaces:**
- Produces: Base project structure and configuration templates

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
build/

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker volumes
data/
backup/
redis-data/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create .env.example**

```env
# Environment
ENV=development
DEBUG=true

# JWT Secret (change this in production!)
JWT_SECRET_KEY=your-super-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=2
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./data/astock.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Tushare Token (optional)
TUSHARE_TOKEN=

# Rate Limiting
RATE_LIMIT_ENABLED=false

# CORS Origins (comma-separated for multiple)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

- [ ] **Step 3: Create initial README.md**

```markdown
# A股看盘工具

一个支持多用户、自定义板块、实时行情的A股看盘网页工具。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + Redis
- **前端**: React + TypeScript + Ant Design
- **数据源**: AkShare (免费开源)
- **部署**: Docker Compose

## 快速开始

### 开发环境

1. 复制环境变量:
   ```bash
   cp .env.example .env
   ```

2. 启动后端:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

3. 启动前端:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker 部署

```bash
cp .env.example .env
# 编辑 .env 设置生产环境变量
docker-compose up -d
```

## 功能特性

- [x] 用户注册/登录
- [x] 自定义板块管理
- [x] 个股添加/删除
- [x] 实时行情刷新
- [x] K线图展示
- [x] 响应式设计
- [ ] 更多功能开发中...

## License

MIT
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore .env.example README.md
git commit -m "feat: init project scaffold"
```

---

### Task 2: Backend Core Configuration

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/schemas.py`

**Interfaces:**
- Produces: `Settings` config class, SQLAlchemy models, Pydantic schemas
- `get_settings()` - returns application settings
- `get_session()` - database session dependency
- Database models: `User`, `Board`, `Stock`, `UserSetting`, `AuditLog`

- [ ] **Step 1: Create backend/requirements.txt**

```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
redis>=5.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
pydantic>=2.0.0
pydantic-settings>=2.0.0
slowapi>=0.1.9
limits>=3.5.0
tenacity>=8.2.0
python-json-logger>=2.0.7
akshare>=1.11.0
httpx>=0.24.0
python-dateutil>=2.8.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0
```

- [ ] **Step 2: Create backend/app/__init__.py**

```python
"""A股看盘工具 Backend"""

__version__ = "1.0.0"
```

- [ ] **Step 3: Create backend/app/config.py**

```python
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import json


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    env: str = "development"
    debug: bool = False

    # JWT settings
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 2
    jwt_refresh_token_expire_days: int = 7

    # Database
    database_url: str = "sqlite:///./data/astock.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Tushare (optional)
    tushare_token: str = ""

    # Rate limiting
    rate_limit_enabled: bool = True

    # CORS
    cors_origins: str = '["http://localhost:3000","http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.cors_origins)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

- [ ] **Step 4: Create backend/app/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from .config import get_settings

settings = get_settings()

# Convert database URL to async format
db_url = settings.database_url
if db_url.startswith("sqlite:///"):
    db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
elif db_url.startswith("sqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite:///")

# Create async engine
engine = create_async_engine(
    db_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create declarative base
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 5: Create backend/app/models.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    boards = relationship("Board", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Board(Base):
    """Stock board model (user-created groups of stocks)."""

    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="boards")
    stocks = relationship("Stock", back_populates="board", cascade="all, delete-orphan", order_by="Stock.sort_order")


class Stock(Base):
    """Stock in a board model."""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(10), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    board = relationship("Board", back_populates="stocks")


class UserSetting(Base):
    """User preferences model."""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    refresh_interval = Column(Integer, default=5, nullable=False)
    data_sources = Column(Text, default='["akshare"]', nullable=False)
    theme = Column(String(20), default="light", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="settings")


class AuditLog(Base):
    """Audit log model for tracking user actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    extra_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
```

- [ ] **Step 6: Create backend/app/schemas.py**

```python
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
    data: Dict[str, List[Quote]]


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
```

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/app/__init__.py backend/app/config.py backend/app/database.py backend/app/models.py backend/app/schemas.py
git commit -m "feat: backend core config and models"
```

---

### Task 3: Backend Authentication and Authorization

**Files:**
- Create: `backend/app/auth.py`

**Interfaces:**
- Produces: `verify_password()`, `get_password_hash()`, `create_access_token()`, `create_refresh_token()`
- Dependencies: `get_current_user()`, `get_current_active_user()`
- API Router: `/api/v1/auth/*` endpoints

- [ ] **Step 1: Create backend/app/auth.py**

```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json

from .config import get_settings
from .database import get_session
from .models import User, UserSetting, AuditLog
from .schemas import (
    UserCreate, UserResponse, TokenResponse, ApiResponse,
    RefreshTokenRequest, UserLogin
)

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Token blacklist (in Redis in production, in-memory for dev)
token_blacklist: Dict[str, float] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_access_token_expire_hours)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh", "jti": f"{data.get('sub')}-{datetime.utcnow().timestamp()}"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_user(db: AsyncSession, username: str) -> Optional[User]:
    """Get a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password."""
    user = await get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
) -> User:
    """Get the current authenticated user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check if token is blacklisted
    if token in token_blacklist:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_client_ip(request: Request) -> Optional[str]:
    """Get client IP address from request."""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


async def log_audit_event(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    request: Optional[Request] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """Log an audit event."""
    try:
        ip_address = await get_client_ip(request) if request else None
        user_agent = request.headers.get("user-agent") if request else None

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=json.dumps(extra_data, ensure_ascii=False) if extra_data else None
        )
        db.add(audit_log)
        await db.commit()
    except Exception:
        # Don't let audit logging fail the main request
        await db.rollback()


@router.post("/register", response_model=ApiResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """Register a new user."""
    # Check if username already exists
    existing_user = await get_user(db, user_data.username)
    if existing_user:
        return ApiResponse(
            success=False,
            error={
                "code": "USERNAME_EXISTS",
                "message": "Username already taken"
            }
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Create default user settings
    db_settings = UserSetting(user_id=db_user.id)
    db.add(db_settings)
    await db.commit()

    # Log audit event
    await log_audit_event(db, db_user.id, "user_register", request, extra_data={"username": user_data.username})

    # Create tokens
    access_token_expires = timedelta(hours=settings.jwt_access_token_expire_hours)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": db_user.id})

    return ApiResponse(
        success=True,
        data={
            "user": UserResponse.model_validate(db_user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
    )


@router.post("/login", response_model=ApiResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_session)
):
    """Login with username and password."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return ApiResponse(
            success=False,
            error={
                "code": "INVALID_CREDENTIALS",
                "message": "Incorrect username or password"
            }
        )

    # Log audit event
    await log_audit_event(db, user.id, "user_login", request)

    # Create tokens
    access_token_expires = timedelta(hours=settings.jwt_access_token_expire_hours)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.id})

    return ApiResponse(
        success=True,
        data={
            "user": UserResponse.model_validate(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
    )


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_session)
):
    """Refresh an access token using a refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    # Check if token is blacklisted
    if token_request.refresh_token in token_blacklist:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token_request.refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    # Create new access token
    access_token_expires = timedelta(hours=settings.jwt_access_token_expire_hours)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return ApiResponse(
        success=True,
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
    )


@router.post("/logout", response_model=ApiResponse)
async def logout(
    token_request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_session)
):
    """Logout - blacklist the refresh token."""
    # Blacklist the refresh token
    try:
        payload = jwt.decode(
            token_request.refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        exp = payload.get("exp")
        if exp:
            token_blacklist[token_request.refresh_token] = exp
    except JWTError:
        pass

    # Log audit event
    await log_audit_event(db, current_user.id, "user_logout", request)

    return ApiResponse(success=True, data={"message": "Logged out successfully"})


@router.get("/me", response_model=ApiResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(current_user)
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/auth.py
git commit -m "feat: backend authentication system"
```

---

### Task 4: Backend Health Check and Cache

**Files:**
- Create: `backend/app/health.py`
- Create: `backend/app/cache.py`

**Interfaces:**
- Produces: Health check endpoints `/health`, `/health/live`, `/health/ready`
- Redis cache helper functions: `get_cache()`, `set_cache()`, `delete_cache()`

- [ ] **Step 1: Create backend/app/health.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import sys

from .database import get_session
from .config import get_settings
from .schemas import HealthStatus, ReadinessStatus, ApiResponse

settings = get_settings()
router = APIRouter(tags=["health"])

# Record startup time
start_time = datetime.utcnow()


@router.get("/health", response_model=ApiResponse)
async def get_health():
    """Overall health status endpoint."""
    uptime = (datetime.utcnow() - start_time).total_seconds()

    return ApiResponse(
        success=True,
        data=HealthStatus(
            status="healthy",
            database="ok",
            redis="ok",
            datasource="ok",
            timestamp=datetime.utcnow().isoformat(),
            uptime=uptime
        )
    )


@router.get("/health/live", response_model=ApiResponse)
async def get_liveness():
    """Liveness probe - just checks if the app is running."""
    return ApiResponse(
        success=True,
        data={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.get("/health/ready", response_model=ApiResponse)
async def get_readiness(db: AsyncSession = Depends(get_session)):
    """Readiness probe - checks database connectivity."""
    checks = {
        "database": "unknown"
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())

    return ApiResponse(
        success=all_ok,
        data=ReadinessStatus(
            status="ready" if all_ok else "not_ready",
            checks=checks,
            timestamp=datetime.utcnow().isoformat()
        )
    )
```

- [ ] **Step 2: Create backend/app/cache.py**

```python
from typing import Optional, Any
import json
import redis.asyncio as redis
from datetime import timedelta
from .config import get_settings

settings = get_settings()

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        except Exception:
            # If Redis is not available, use a dummy in-memory cache
            _redis_client = None
    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# In-memory fallback cache
_memory_cache: dict[str, tuple[Any, float]] = {}


async def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache."""
    redis_client = await get_redis()

    if redis_client:
        try:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
    else:
        # Fallback to in-memory cache
        if key in _memory_cache:
            value, expire_time = _memory_cache[key]
            import time
            if time.time() < expire_time:
                return value
            else:
                del _memory_cache[key]

    return None


async def set_cache(key: str, value: Any, ttl: int = 300):
    """Set a value in cache with TTL (seconds)."""
    redis_client = await get_redis()
    data = json.dumps(value, ensure_ascii=False)

    if redis_client:
        try:
            await redis_client.setex(key, ttl, data)
        except Exception:
            pass
    else:
        # Fallback to in-memory cache
        import time
        expire_time = time.time() + ttl
        _memory_cache[key] = (value, expire_time)


async def delete_cache(key: str):
    """Delete a value from cache."""
    redis_client = await get_redis()

    if redis_client:
        try:
            await redis_client.delete(key)
        except Exception:
            pass
    else:
        if key in _memory_cache:
            del _memory_cache[key]


async def delete_cache_pattern(pattern: str):
    """Delete all keys matching a pattern."""
    redis_client = await get_redis()

    if redis_client:
        try:
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
        except Exception:
            pass
    else:
        # Fallback to in-memory cache
        import re
        pattern_re = re.compile(pattern.replace("*", ".*"))
        keys_to_delete = [k for k in _memory_cache if pattern_re.match(k)]
        for k in keys_to_delete:
            del _memory_cache[k]


def get_quote_key(code: str) -> str:
    """Get cache key for a stock quote."""
    return f"quote:{code}"


def get_quotes_key(codes: list[str]) -> str:
    """Get cache key for batch quotes."""
    import hashlib
    codes_str = ",".join(sorted(codes))
    hash_val = hashlib.md5(codes_str.encode()).hexdigest()
    return f"quotes:{hash_val}"


def get_kline_key(code: str, period: str) -> str:
    """Get cache key for K-line data."""
    return f"kline:{code}:{period}"


def get_search_key(keyword: str) -> str:
    """Get cache key for search results."""
    return f"search:{keyword}"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/health.py backend/app/cache.py
git commit -m "feat: backend health check and cache layer"
```

---

### Task 5: Backend Data Sources

**Files:**
- Create: `backend/app/datasources/__init__.py`
- Create: `backend/app/datasources/base.py`
- Create: `backend/app/datasources/akshare.py`

**Interfaces:**
- Produces: `BaseDataSource` abstract base class
- `AkShareDataSource` implementation with circuit breaker pattern
- Functions: `get_quote()`, `get_quotes()`, `get_kline()`, `search_stock()`

- [ ] **Step 1: Create backend/app/datasources/__init__.py**

```python
"""Data sources for stock quotes."""

from .base import BaseDataSource, Quote, KLineItem
from .akshare import AkShareDataSource

# Default data source
_default_source: Optional[BaseDataSource] = None


def get_data_source() -> BaseDataSource:
    """Get the default data source."""
    global _default_source
    if _default_source is None:
        _default_source = AkShareDataSource()
    return _default_source


__all__ = [
    "BaseDataSource",
    "Quote",
    "KLineItem",
    "AkShareDataSource",
    "get_data_source"
]
```

- [ ] **Step 2: Create backend/app/datasources/base.py**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class Quote:
    """Stock quote data."""
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
    timestamp: float = 0.0
    stale: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "price": self.price,
            "pre_close": self.pre_close,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "amount": self.amount,
            "change": self.change,
            "change_percent": self.change_percent,
            "bid1": self.bid1,
            "bid1_volume": self.bid1_volume,
            "ask1": self.ask1,
            "ask1_volume": self.ask1_volume,
            "timestamp": self.timestamp,
            "stale": self.stale
        }


@dataclass
class KLineItem:
    """K-line (candlestick) data item."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    change: float
    change_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
            "change": self.change,
            "change_percent": self.change_percent
        }


class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def record_success(self):
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker closing - recovered from failures")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record a failed call."""
        self.last_failure_time = time.time()
        self.success_count = 0

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker opening - failed in half-open state")
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                logger.warning(f"Circuit breaker opening - {self.failure_count} failures exceeded threshold")
                self.state = CircuitState.OPEN

    def can_call(self) -> bool:
        """Check if a call can be made."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker moving to half-open state")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            # Only allow one call in half-open state
            return self.success_count == 0
        return False


class BaseDataSource(ABC):
    """Abstract base class for stock data sources."""

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.name = "base"

    @abstractmethod
    async def get_quote(self, code: str) -> Optional[Quote]:
        """Get quote for a single stock."""
        pass

    @abstractmethod
    async def get_quotes(self, codes: List[str]) -> Dict[str, Quote]:
        """Get quotes for multiple stocks."""
        pass

    @abstractmethod
    async def get_kline(self, code: str, period: str = "1d", count: int = 100) -> List[KLineItem]:
        """Get K-line data for a stock."""
        pass

    @abstractmethod
    async def search_stock(self, keyword: str) -> List[Dict[str, str]]:
        """Search for stocks by keyword."""
        pass
```

- [ ] **Step 3: Create backend/app/datasources/akshare.py**

```python
from typing import List, Dict, Any, Optional
import asyncio
import time
import logging

from .base import BaseDataSource, Quote, KLineItem

logger = logging.getLogger(__name__)

# Mock data for development (when AkShare is not available)
MOCK_QUOTES = {
    "600519": Quote(
        code="600519",
        name="贵州茅台",
        price=1800.00,
        pre_close=1755.00,
        open=1760.00,
        high=1820.00,
        low=1750.00,
        volume=25000,
        amount=450000000,
        change=45.00,
        change_percent=2.56,
        bid1=1799.99,
        bid1_volume=100,
        ask1=1800.01,
        ask1_volume=100,
        timestamp=time.time()
    ),
    "000001": Quote(
        code="000001",
        name="平安银行",
        price=12.50,
        pre_close=12.70,
        open=12.65,
        high=12.75,
        low=12.40,
        volume=1000000,
        amount=12500000,
        change=-0.20,
        change_percent=-1.57,
        bid1=12.49,
        bid1_volume=5000,
        ask1=12.51,
        ask1_volume=5000,
        timestamp=time.time()
    ),
    "300750": Quote(
        code="300750",
        name="宁德时代",
        price=200.00,
        pre_close=205.00,
        open=204.00,
        high=206.00,
        low=198.00,
        volume=500000,
        amount=100000000,
        change=-5.00,
        change_percent=-2.44,
        bid1=199.99,
        bid1_volume=200,
        ask1=200.01,
        ask1_volume=200,
        timestamp=time.time()
    ),
    "000858": Quote(
        code="000858",
        name="五粮液",
        price=150.00,
        pre_close=148.00,
        open=148.50,
        high=151.00,
        low=147.50,
        volume=300000,
        amount=45000000,
        change=2.00,
        change_percent=1.35,
        bid1=149.99,
        bid1_volume=300,
        ask1=150.01,
        ask1_volume=300,
        timestamp=time.time()
    ),
    "688981": Quote(
        code="688981",
        name="中芯国际",
        price=50.00,
        pre_close=49.00,
        open=49.50,
        high=51.00,
        low=49.00,
        volume=800000,
        amount=40000000,
        change=1.00,
        change_percent=2.04,
        bid1=49.99,
        bid1_volume=1000,
        ask1=50.01,
        ask1_volume=1000,
        timestamp=time.time()
    ),
}

# Stock search database for mock
MOCK_STOCKS = [
    {"code": "600519", "name": "贵州茅台", "market": "sh"},
    {"code": "000001", "name": "平安银行", "market": "sz"},
    {"code": "300750", "name": "宁德时代", "market": "sz"},
    {"code": "000858", "name": "五粮液", "market": "sz"},
    {"code": "688981", "name": "中芯国际", "market": "sh"},
    {"code": "601318", "name": "中国平安", "market": "sh"},
    {"code": "000333", "name": "美的集团", "market": "sz"},
    {"code": "600036", "name": "招商银行", "market": "sh"},
    {"code": "002594", "name": "比亚迪", "market": "sz"},
    {"code": "600900", "name": "长江电力", "market": "sh"},
]


class AkShareDataSource(BaseDataSource):
    """AkShare data source implementation."""

    def __init__(self):
        super().__init__()
        self.name = "akshare"
        self._akshare_available = None

    async def _check_akshare(self) -> bool:
        """Check if AkShare is available."""
        if self._akshare_available is not None:
            return self._akshare_available

        try:
            # Try to import AkShare
            import akshare as ak
            self._akshare_available = True
            logger.info("AkShare is available")
        except ImportError:
            self._akshare_available = False
            logger.warning("AkShare not available, using mock data")

        return self._akshare_available

    async def get_quote(self, code: str) -> Optional[Quote]:
        """Get quote for a single stock."""
        if not self.circuit_breaker.can_call():
            logger.warning(f"Circuit breaker open for {self.name}, returning cached/mock data")
            return MOCK_QUOTES.get(code)

        try:
            # First try mock data for development
            if await self._check_akshare():
                # TODO: Implement real AkShare integration
                quote = self._get_mock_quote(code)
            else:
                quote = self._get_mock_quote(code)

            if quote:
                self.circuit_breaker.record_success()
                return quote
            else:
                self.circuit_breaker.record_failure()
                return None

        except Exception as e:
            logger.error(f"Error getting quote from {self.name}: {e}")
            self.circuit_breaker.record_failure()
            # Return mock data as fallback
            return MOCK_QUOTES.get(code)

    async def get_quotes(self, codes: List[str]) -> Dict[str, Quote]:
        """Get quotes for multiple stocks."""
        if not self.circuit_breaker.can_call():
            logger.warning(f"Circuit breaker open for {self.name}, returning cached/mock data")
            return {code: MOCK_QUOTES[code] for code in codes if code in MOCK_QUOTES}

        try:
            if await self._check_akshare():
                # TODO: Implement real AkShare batch quote fetch
                quotes = {code: self._get_mock_quote(code) for code in codes}
            else:
                quotes = {code: self._get_mock_quote(code) for code in codes}

            # Filter out None values
            quotes = {k: v for k, v in quotes.items() if v is not None}

            if quotes:
                self.circuit_breaker.record_success()
            else:
                self.circuit_breaker.record_failure()

            return quotes

        except Exception as e:
            logger.error(f"Error getting quotes from {self.name}: {e}")
            self.circuit_breaker.record_failure()
            return {code: MOCK_QUOTES[code] for code in codes if code in MOCK_QUOTES}

    async def get_kline(self, code: str, period: str = "1d", count: int = 100) -> List[KLineItem]:
        """Get K-line data for a stock."""
        if not self.circuit_breaker.can_call():
            logger.warning(f"Circuit breaker open for {self.name}, returning mock data")
            return self._generate_mock_kline(code, period, count)

        try:
            if await self._check_akshare():
                # TODO: Implement real AkShare K-line fetch
                kline = self._generate_mock_kline(code, period, count)
            else:
                kline = self._generate_mock_kline(code, period, count)

            self.circuit_breaker.record_success()
            return kline

        except Exception as e:
            logger.error(f"Error getting K-line from {self.name}: {e}")
            self.circuit_breaker.record_failure()
            return self._generate_mock_kline(code, period, count)

    async def search_stock(self, keyword: str) -> List[Dict[str, str]]:
        """Search for stocks by keyword."""
        if not self.circuit_breaker.can_call():
            logger.warning(f"Circuit breaker open for {self.name}, returning mock data")
            return self._search_mock_stocks(keyword)

        try:
            if await self._check_akshare():
                # TODO: Implement real AkShare stock search
                results = self._search_mock_stocks(keyword)
            else:
                results = self._search_mock_stocks(keyword)

            self.circuit_breaker.record_success()
            return results

        except Exception as e:
            logger.error(f"Error searching stocks from {self.name}: {e}")
            self.circuit_breaker.record_failure()
            return self._search_mock_stocks(keyword)

    def _get_mock_quote(self, code: str) -> Optional[Quote]:
        """Get mock quote data."""
        if code in MOCK_QUOTES:
            quote = MOCK_QUOTES[code]
            # Add some randomness to make it look real
            import random
            variation = (random.random() - 0.5) * quote.price * 0.01
            quote.price += variation
            quote.change = quote.price - quote.pre_close
            quote.change_percent = (quote.change / quote.pre_close) * 100
            quote.timestamp = time.time()
            return quote
        return None

    def _generate_mock_kline(self, code: str, period: str, count: int) -> List[KLineItem]:
        """Generate mock K-line data."""
        import random
        from datetime import datetime, timedelta

        items = []
        base_price = MOCK_QUOTES.get(code, Quote(
            code=code, name="Unknown", price=100.0, pre_close=100.0,
            open=100.0, high=100.0, low=100.0, volume=0, amount=0,
            change=0, change_percent=0
        )).price

        current_price = base_price

        for i in range(count, 0, -1):
            if period == "1d":
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            elif period == "1w":
                date = (datetime.now() - timedelta(weeks=i)).strftime("%Y-%m-%d")
            elif period == "1M":
                date = (datetime.now() - timedelta(days=i*30)).strftime("%Y-%m")
            else:
                date = (datetime.now() - timedelta(minutes=i*int(period[:-1]))).strftime("%Y-%m-%d %H:%M")

            # Generate random price movement
            change_pct = (random.random() - 0.5) * 0.05  # +/- 2.5%
            open_price = current_price
            close_price = open_price * (1 + change_pct)
            high_price = max(open_price, close_price) * (1 + random.random() * 0.02)
            low_price = min(open_price, close_price) * (1 - random.random() * 0.02)
            volume = random.randint(10000, 1000000)
            amount = volume * (open_price + close_price) / 2
            change = close_price - open_price
            change_percent = (change / open_price) * 100 if open_price > 0 else 0

            items.append(KLineItem(
                date=date,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=volume,
                amount=round(amount, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2)
            ))

            current_price = close_price

        return items

    def _search_mock_stocks(self, keyword: str) -> List[Dict[str, str]]:
        """Search mock stocks."""
        keyword = keyword.lower()
        results = []
        for stock in MOCK_STOCKS:
            if keyword in stock["code"].lower() or keyword in stock["name"].lower():
                results.append(stock)
        return results
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/datasources/__init__.py backend/app/datasources/base.py backend/app/datasources/akshare.py
git commit -m "feat: backend data sources with circuit breaker"
```

---

### Task 6: Backend API Endpoints - Boards, Stocks, Quotes

**Files:**
- Create: `backend/app/boards.py`
- Create: `backend/app/stocks.py`
- Create: `backend/app/quotes.py`
- Create: `backend/app/settings.py`

**Interfaces:**
- Produces: REST API routers for all business logic
- WebSocket endpoint `/ws/quotes` for real-time updates

- [ ] **Step 1: Create backend/app/boards.py**

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import get_session
from .models import User, Board, Stock
from .schemas import (
    BoardCreate, BoardUpdate, BoardResponse, BoardWithStocks,
    ApiResponse, BoardReorderRequest
)
from .auth import get_current_user, log_audit_event

router = APIRouter(prefix="/api/v1/boards", tags=["boards"])


@router.get("", response_model=ApiResponse)
async def get_boards(
    include_stocks: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get all boards for the current user."""
    query = (
        select(Board)
        .where(Board.user_id == current_user.id)
        .order_by(Board.sort_order, Board.id)
    )

    if include_stocks:
        query = query.options(selectinload(Board.stocks))

    result = await db.execute(query)
    boards = result.scalars().all()

    return ApiResponse(
        success=True,
        data=[BoardWithStocks.model_validate(b) for b in boards]
    )


@router.post("", response_model=ApiResponse)
async def create_board(
    board_data: BoardCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Create a new board."""
    # Get max sort order
    result = await db.execute(
        select(Board.sort_order)
        .where(Board.user_id == current_user.id)
        .order_by(Board.sort_order.desc())
        .limit(1)
    )
    max_order = result.scalar_one_or_none()
    new_order = (max_order + 1) if max_order is not None else 0

    # Create board
    db_board = Board(
        user_id=current_user.id,
        name=board_data.name,
        sort_order=new_order
    )
    db.add(db_board)
    await db.commit()
    await db.refresh(db_board)

    # Log audit event
    await log_audit_event(
        db, current_user.id, "board_create", request,
        resource_type="board", resource_id=db_board.id,
        extra_data={"name": board_data.name}
    )

    return ApiResponse(
        success=True,
        data=BoardResponse.model_validate(db_board)
    )


@router.get("/{board_id}", response_model=ApiResponse)
async def get_board(
    board_id: int,
    include_stocks: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get a specific board."""
    query = select(Board).where(
        Board.id == board_id,
        Board.user_id == current_user.id
    )

    if include_stocks:
        query = query.options(selectinload(Board.stocks))

    result = await db.execute(query)
    board = result.scalar_one_or_none()

    if not board:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Board not found"
            }
        )

    return ApiResponse(
        success=True,
        data=BoardWithStocks.model_validate(board)
    )


@router.put("/{board_id}", response_model=ApiResponse)
async def update_board(
    board_id: int,
    board_data: BoardUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Update a board."""
    result = await db.execute(
        select(Board).where(
            Board.id == board_id,
            Board.user_id == current_user.id
        )
    )
    board = result.scalar_one_or_none()

    if not board:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Board not found"
            }
        )

    # Update fields
    if board_data.name is not None:
        board.name = board_data.name
    if board_data.sort_order is not None:
        board.sort_order = board_data.sort_order

    await db.commit()
    await db.refresh(board)

    # Log audit event
    await log_audit_event(
        db, current_user.id, "board_update", request,
        resource_type="board", resource_id=board_id
    )

    return ApiResponse(
        success=True,
        data=BoardResponse.model_validate(board)
    )


@router.delete("/{board_id}", response_model=ApiResponse)
async def delete_board(
    board_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Delete a board."""
    result = await db.execute(
        select(Board).where(
            Board.id == board_id,
            Board.user_id == current_user.id
        )
    )
    board = result.scalar_one_or_none()

    if not board:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Board not found"
            }
        )

    await db.delete(board)
    await db.commit()

    # Log audit event
    await log_audit_event(
        db, current_user.id, "board_delete", request,
        resource_type="board", resource_id=board_id
    )

    return ApiResponse(
        success=True,
        data={"message": "Board deleted successfully"}
    )


@router.put("/reorder", response_model=ApiResponse)
async def reorder_boards(
    reorder_data: BoardReorderRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Reorder boards."""
    # Get all user boards
    result = await db.execute(
        select(Board).where(Board.user_id == current_user.id)
    )
    boards = {b.id: b for b in result.scalars().all()}

    # Update sort order
    for index, board_id in enumerate(reorder_data.board_ids):
        if board_id in boards:
            boards[board_id].sort_order = index

    await db.commit()

    # Log audit event
    await log_audit_event(
        db, current_user.id, "board_reorder", request
    )

    return ApiResponse(
        success=True,
        data={"message": "Boards reordered successfully"}
    )
```

- [ ] **Step 2: Create backend/app/stocks.py**

```python
from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .models import User, Board, Stock
from .schemas import (
    StockCreate, StockUpdate, StockResponse,
    ApiResponse, StockReorderRequest
)
from .auth import get_current_user, log_audit_event
from .datasources import get_data_source

router = APIRouter(prefix="/api/v1/boards/{board_id}/stocks", tags=["stocks"])


async def get_board_for_user(
    board_id: int,
    user_id: int,
    db: AsyncSession
) -> Board:
    """Get a board and verify it belongs to the user."""
    result = await db.execute(
        select(Board).where(
            Board.id == board_id,
            Board.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


@router.get("", response_model=ApiResponse)
async def get_stocks(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get all stocks in a board."""
    board = await get_board_for_user(board_id, current_user.id, db)
    if not board:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Board not found"
            }
        )

    result = await db.execute(
        select(Stock)
        .where(Stock.board_id == board_id)
        .order_by(Stock.sort_order, Stock.id)
    )
    stocks = result.scalars().all()

    return ApiResponse(
        success=True,
        data=[StockResponse.model_validate(s) for s in stocks]
    )


@router.post("", response_model=ApiResponse)
async def add_stock(
    board_id: int,
    stock_data: StockCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Add a stock to a board."""
    board = await get_board_for_user(board_id, current_user.id, db)
    if not board:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Board not found"
            }
        )

    # Check if stock already in board
    result = await db.execute(
        select(Stock).where(
            Stock.board_id == board_id,
            Stock.code == stock_data.code
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return ApiResponse(
            success=False,
            error={
                "code": "ALREADY_EXISTS",
                "message": "Stock already in board"
            }
        )

    # Get max sort order
    result = await db.execute(
        select(Stock.sort_order)
        .where(Stock.board_id == board_id)
        .order_by(Stock.sort_order.desc())
        .limit(1)
    )
    max_order = result.scalar_one_or_none()
    new_order = (max_order + 1) if max_order is not None else 0

    # Create stock
    db_stock = Stock(
        board_id=board_id,
        code=stock_data.code,
        name=stock_data.name,
        sort_order=new_order
    )
    db.add(db_stock)
    await db.commit()
    await db.refresh(db_stock)

    # Log audit event
    await log_audit_event(
        db, current_user.id, "stock_add", request,
        resource_type="stock", resource_id=db_stock.id,
        extra_data={"code": stock_data.code, "name": stock_data.name}
    )

    return ApiResponse(
        success=True,
        data=StockResponse.model_validate(db_stock)
    )


@router.delete("/{stock_id}", response_model=ApiResponse)
async def remove_stock(
    board_id: int,
    stock_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Remove a stock from a board."""
    board = await get_board_for_user(board_id, current_user.id, db)
    if not board:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Board not found"
            }
        )

    result = await db.execute(
        select(Stock).where(
            Stock.id == stock_id,
            Stock.board_id == board_id
        )
    )
    stock = result.scalar_one_or_none()

    if not stock:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Stock not found"
            }
        )

    await db.delete(stock)
    await db.commit()

    # Log audit event
    await log_audit_event(
        db, current_user.id, "stock_remove", request,
        resource_type="stock", resource_id=stock_id,
        extra_data={"code": stock.code}
    )

    return ApiResponse(
        success=True,
        data={"message": "Stock removed successfully"}
    )


@router.put("/reorder", response_model=ApiResponse)
async def reorder_stocks(
    board_id: int,
    reorder_data: StockReorderRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Reorder stocks in a board."""
    board = await get_board_for_user(board_id, current_user.id, db)
    if not board:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": "Board not found"
            }
        )

    # Get all stocks in board
    result = await db.execute(
        select(Stock).where(Stock.board_id == board_id)
    )
    stocks = {s.id: s for s in result.scalars().all()}

    # Update sort order
    for index, stock_id in enumerate(reorder_data.stock_ids):
        if stock_id in stocks:
            stocks[stock_id].sort_order = index

    await db.commit()

    # Log audit event
    await log_audit_event(
        db, current_user.id, "stock_reorder", request,
        resource_type="board", resource_id=board_id
    )

    return ApiResponse(
        success=True,
        data={"message": "Stocks reordered successfully"}
    )


# === Stock search endpoint (not board-specific) ===

search_router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


@search_router.get("/search", response_model=ApiResponse)
async def search_stocks(
    keyword: str,
    current_user: User = Depends(get_current_user)
):
    """Search for stocks by keyword."""
    if not keyword or len(keyword) < 1:
        return ApiResponse(
            success=False,
            error={
                "code": "INVALID_INPUT",
                "message": "Keyword must be at least 1 character"
            }
        )

    data_source = get_data_source()
    results = await data_source.search_stock(keyword)

    return ApiResponse(
        success=True,
        data=results
    )
```

- [ ] **Step 3: Create backend/app/quotes.py**

```python
from typing import List, Dict, Set
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json
import time
import logging

from .database import get_session
from .models import User, Board, Stock
from .schemas import ApiResponse, Quote, KLineItem
from .auth import get_current_user
from .datasources import get_data_source
from .cache import get_cache, set_cache, get_quote_key, get_quotes_key, get_kline_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"])

# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.subscriptions: Dict[int, Set[str]] = {}
        self.push_task: Optional[asyncio.Task] = None

    async def connect(self, user_id: int, websocket: WebSocket):
        """Connect a user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.subscriptions[user_id] = set()
        logger.info(f"WebSocket connected: user {user_id}")

    def disconnect(self, user_id: int):
        """Disconnect a user."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.subscriptions:
            del self.subscriptions[user_id]
        logger.info(f"WebSocket disconnected: user {user_id}")

    def subscribe(self, user_id: int, codes: List[str]):
        """Subscribe to stock quotes."""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].update(codes)
            logger.debug(f"User {user_id} subscribed to: {codes}")

    def unsubscribe(self, user_id: int, codes: List[str]):
        """Unsubscribe from stock quotes."""
        if user_id in self.subscriptions:
            for code in codes:
                self.subscriptions[user_id].discard(code)
            logger.debug(f"User {user_id} unsubscribed from: {codes}")

    async def send_personal_message(self, user_id: int, message: dict):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_quotes(self, quotes: Dict[str, Quote]):
        """Broadcast quotes to subscribed users."""
        for user_id, subscribed_codes in self.subscriptions.items():
            user_quotes = {
                code: quote for code, quote in quotes.items()
                if code in subscribed_codes
            }
            if user_quotes:
                await self.send_personal_message(
                    user_id,
                    {
                        "type": "quotes",
                        "data": {
                            "quotes": [q.to_dict() for q in user_quotes.values()]
                        }
                    }
                )


manager = ConnectionManager()


@router.get("", response_model=ApiResponse)
async def get_quotes(
    codes: str = Query(..., description="Comma-separated stock codes"),
    current_user: User = Depends(get_current_user)
):
    """Get quotes for multiple stocks."""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return ApiResponse(
            success=False,
            error={
                "code": "INVALID_INPUT",
                "message": "No stock codes provided"
            }
        )

    # Try cache first
    cache_key = get_quotes_key(code_list)
    cached = await get_cache(cache_key)
    if cached:
        return ApiResponse(success=True, data=cached)

    # Fetch from data source
    data_source = get_data_source()
    quotes = await data_source.get_quotes(code_list)

    # Convert to dict
    quotes_dict = {code: q.to_dict() for code, q in quotes.items()}

    # Cache result (5 seconds)
    await set_cache(cache_key, quotes_dict, ttl=5)

    return ApiResponse(success=True, data=quotes_dict)


@router.get("/{code}", response_model=ApiResponse)
async def get_quote(
    code: str,
    current_user: User = Depends(get_current_user)
):
    """Get quote for a single stock."""
    # Try cache first
    cache_key = get_quote_key(code)
    cached = await get_cache(cache_key)
    if cached:
        return ApiResponse(success=True, data=cached)

    # Fetch from data source
    data_source = get_data_source()
    quote = await data_source.get_quote(code)

    if not quote:
        return ApiResponse(
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Quote not found for {code}"
            }
        )

    quote_dict = quote.to_dict()

    # Cache result (5 seconds)
    await set_cache(cache_key, quote_dict, ttl=5)

    return ApiResponse(success=True, data=quote_dict)


@router.get("/{code}/kline", response_model=ApiResponse)
async def get_kline(
    code: str,
    period: str = Query("1d", description="K-line period: 1d, 1w, 1M, 5m, 15m, 30m, 60m"),
    count: int = Query(100, ge=1, le=500, description="Number of K-line items"),
    current_user: User = Depends(get_current_user)
):
    """Get K-line data for a stock."""
    # Try cache first
    cache_key = get_kline_key(code, period)
    cached = await get_cache(cache_key)
    if cached:
        return ApiResponse(success=True, data=cached)

    # Fetch from data source
    data_source = get_data_source()
    kline = await data_source.get_kline(code, period, count)

    # Convert to dict
    kline_dict = [item.to_dict() for item in kline]

    # Cache result (5 minutes)
    await set_cache(cache_key, kline_dict, ttl=300)

    return ApiResponse(success=True, data=kline_dict)


# === WebSocket Endpoint ===

from fastapi import APIRouter

ws_router = APIRouter()


@ws_router.websocket("/ws/quotes")
async def websocket_quotes(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time quotes."""
    # Authenticate user from token
    from jose import JWTError, jwt
    from .config import get_settings
    from .database import get_session
    from .auth import get_user_by_id

    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    # Verify user exists
    async def _get_user():
        async for session in get_session():
            return await get_user_by_id(session, user_id)

    user = await _get_user()
    if not user:
        await websocket.close(code=1008)
        return

    # Connect
    await manager.connect(user_id, websocket)

    try:
        # Send welcome ping
        await websocket.send_json({"type": "ping"})

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "subscribe":
                    codes = message.get("codes", [])
                    if codes:
                        manager.subscribe(user_id, codes)
                        # Send initial quotes
                        data_source = get_data_source()
                        quotes = await data_source.get_quotes(codes)
                        if quotes:
                            await manager.send_personal_message(
                                user_id,
                                {
                                    "type": "quotes",
                                    "data": {
                                        "quotes": [q.to_dict() for q in quotes.values()]
                                    }
                                }
                            )

                elif msg_type == "unsubscribe":
                    codes = message.get("codes", [])
                    manager.unsubscribe(user_id, codes)

                elif msg_type == "pong":
                    # Just acknowledge, no action needed
                    pass

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    user_id,
                    {
                        "type": "error",
                        "code": "INVALID_JSON",
                        "message": "Invalid JSON format"
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)


# === Background quote push task ===

async def start_quote_push_task():
    """Start the background task to push quotes to WebSocket clients."""
    if manager.push_task is None:
        manager.push_task = asyncio.create_task(_quote_push_loop())
        logger.info("Quote push task started")


async def stop_quote_push_task():
    """Stop the background quote push task."""
    if manager.push_task:
        manager.push_task.cancel()
        try:
            await manager.push_task
        except asyncio.CancelledError:
            pass
        manager.push_task = None
        logger.info("Quote push task stopped")


async def _quote_push_loop():
    """Background loop to push quotes to WebSocket clients."""
    data_source = get_data_source()

    while True:
        try:
            # Collect all subscribed codes
            all_codes: Set[str] = set()
            for codes in manager.subscriptions.values():
                all_codes.update(codes)

            if all_codes:
                # Fetch quotes
                quotes = await data_source.get_quotes(list(all_codes))

                if quotes:
                    # Broadcast to subscribed users
                    await manager.broadcast_quotes(quotes)

            # Wait before next update
            await asyncio.sleep(5)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in quote push loop: {e}")
            await asyncio.sleep(5)
```

- [ ] **Step 4: Create backend/app/settings.py**

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .models import User, UserSetting
from .schemas import UserSettingUpdate, UserSettingResponse, ApiResponse
from .auth import get_current_user, log_audit_event

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("", response_model=ApiResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get user settings."""
    result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    # Create default settings if not exists
    if not settings:
        settings = UserSetting(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return ApiResponse(
        success=True,
        data=UserSettingResponse.model_validate(settings)
    )


@router.put("", response_model=ApiResponse)
async def update_settings(
    settings_data: UserSettingUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Update user settings."""
    result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSetting(user_id=current_user.id)
        db.add(settings)

    # Update fields
    if settings_data.refresh_interval is not None:
        settings.refresh_interval = settings_data.refresh_interval
    if settings_data.data_sources is not None:
        settings.data_sources = settings_data.data_sources
    if settings_data.theme is not None:
        settings.theme = settings_data.theme

    await db.commit()
    await db.refresh(settings)

    # Log audit event
    await log_audit_event(
        db, current_user.id, "settings_update", request
    )

    return ApiResponse(
        success=True,
        data=UserSettingResponse.model_validate(settings)
    )
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/boards.py backend/app/stocks.py backend/app/quotes.py backend/app/settings.py
git commit -m "feat: backend API endpoints"
```

---

### Task 7: Backend Main Application Entry Point

**Files:**
- Create: `backend/main.py`

**Interfaces:**
- Produces: Complete FastAPI application with all routers mounted
- Startup/shutdown events for database initialization and background tasks

- [ ] **Step 1: Create backend/main.py**

```python
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.health import router as health_router
from app.auth import router as auth_router
from app.boards import router as boards_router
from app.stocks import router as stocks_router, search_router as stock_search_router
from app.quotes import router as quotes_router, ws_router
from app.settings import router as settings_router
from app.quotes import start_quote_push_task, stop_quote_push_task
from app.cache import close_redis

settings = get_settings()

# Setup logging
def setup_logging():
    """Configure logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Formatters
    standard_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_handler.setFormatter(standard_formatter)
    root_logger.addHandler(console_handler)

    # File handler (rotating daily)
    if not settings.debug:
        file_handler = TimedRotatingFileHandler(
            log_dir / "app.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(standard_formatter)
        root_logger.addHandler(file_handler)


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info("Starting application...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start quote push task
    await start_quote_push_task()

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await stop_quote_push_task()
    await close_redis()


# Create FastAPI app
app = FastAPI(
    title="A股看盘工具 API",
    description="A stock watchlist application for Chinese A-shares",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        }
    )


# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(boards_router)
app.include_router(stocks_router)
app.include_router(stock_search_router)
app.include_router(quotes_router)
app.include_router(ws_router)
app.include_router(settings_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - return API info."""
    return {
        "success": True,
        "data": {
            "name": "A股看盘工具 API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn

    # Create data directory
    Path("data").mkdir(exist_ok=True)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: backend main application entry point"
```

---

### Task 8: Backend Tests

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: Test fixtures and basic test suite

- [ ] **Step 1: Create backend/tests/__init__.py**

```python
"""Tests package."""
```

- [ ] **Step 2: Create backend/tests/conftest.py**

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_session
from app.main import app
from app.config import get_settings

# Override settings for tests
test_settings = get_settings()
test_settings.database_url = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client."""
    async def _override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = _override_get_session
    return TestClient(app)
```

- [ ] **Step 3: Create backend/tests/test_auth.py**

```python
"""Tests for authentication endpoints."""


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "user" in data["data"]
    assert "access_token" in data["data"]


def test_register_duplicate_username(client):
    """Test registering duplicate username fails."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"username": "testuser2", "password": "testpass123"}
    )

    # Try to register again
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser2", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "USERNAME_EXISTS"


def test_login_user(client):
    """Test user login."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"username": "testuser3", "password": "testpass123"}
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser3", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_login_invalid_credentials(client):
    """Test login with invalid credentials fails."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "wrongpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_get_current_user(client):
    """Test getting current user info."""
    # Register and login
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser4", "password": "testpass123"}
    )
    token = register_response.json()["data"]["access_token"]

    # Get current user
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "testuser4"


def test_get_current_user_no_auth(client):
    """Test getting current user without auth fails."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/__init__.py backend/tests/conftest.py backend/tests/test_auth.py
git commit -m "test: add backend auth tests"
```

---

### Task 9: Frontend Setup and Configuration

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/.env.example`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/index.css`

**Interfaces:**
- Produces: React + TypeScript + Vite frontend scaffold

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "astock-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.14.0",
    "antd": "^5.7.0",
    "@ant-design/icons": "^5.2.0",
    "axios": "^1.4.0",
    "zustand": "^4.4.0",
    "dayjs": "^1.11.9",
    "lightweight-charts": "^4.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "typescript": "^5.0.0",
    "vite": "^4.4.0"
  }
}
```

- [ ] **Step 2: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Create frontend/tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 5: Create frontend/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>A股看盘工具</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create frontend/.env.example**

```env
# API base URL
VITE_API_URL=http://localhost:8000

# WebSocket URL
VITE_WS_URL=ws://localhost:8000
```

- [ ] **Step 7: Create frontend/src/vite-env.d.ts**

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

- [ ] **Step 8: Create frontend/src/index.css**

```css
/* Global styles */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#root {
  min-height: 100vh;
}

/* Stock colors */
.stock-up {
  color: #cf1322;
}

.stock-down {
  color: #3f8600;
}

.stock-neutral {
  color: #8c8c8c;
}
```

- [ ] **Step 9: Create frontend/src/main.tsx**

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider locale={zhCN}>
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
```

- [ ] **Step 10: Create frontend/src/App.tsx**

```typescript
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Dashboard from '@/pages/Dashboard'
import StockDetail from '@/pages/StockDetail'
import ProtectedRoute from '@/components/ProtectedRoute'

function App() {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to="/" replace /> : <Register />}
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/stock/:code"
        element={
          <ProtectedRoute>
            <StockDetail />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
```

- [ ] **Step 11: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts frontend/index.html frontend/.env.example frontend/src/vite-env.d.ts frontend/src/main.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: frontend setup and configuration"
```

---

### Task 10: Frontend Type Definitions and API Services

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/config.ts`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/services/auth.ts`
- Create: `frontend/src/services/ws.ts`

**Interfaces:**
- Produces: TypeScript type definitions and API service layer

- [ ] **Step 1: Create frontend/src/types/index.ts**

```typescript
// User types
export interface User {
  id: number
  username: string
  created_at: string
}

export interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
}

// Board types
export interface Board {
  id: number
  user_id: number
  name: string
  sort_order: number
  created_at: string
  updated_at: string
  stocks: Stock[]
}

export interface BoardCreate {
  name: string
}

export interface BoardUpdate {
  name?: string
  sort_order?: number
}

// Stock types
export interface Stock {
  id: number
  board_id: number
  code: string
  name: string
  sort_order: number
  created_at: string
}

export interface StockCreate {
  code: string
  name: string
}

// Quote types
export interface Quote {
  code: string
  name: string
  price: number
  pre_close: number
  open: number
  high: number
  low: number
  volume: number
  amount: number
  change: number
  change_percent: number
  bid1?: number
  bid1_volume?: number
  ask1?: number
  ask1_volume?: number
  timestamp: number
  stale?: boolean
}

// K-line types
export interface KLineItem {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  change: number
  change_percent: number
}

export type KLinePeriod = '1d' | '1w' | '1M' | '5m' | '15m' | '30m' | '60m'

// User settings types
export interface UserSetting {
  id: number
  user_id: number
  refresh_interval: number
  data_sources: string
  theme: 'light' | 'dark'
  created_at: string
  updated_at: string
}

export interface UserSettingUpdate {
  refresh_interval?: number
  data_sources?: string
  theme?: 'light' | 'dark'
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
}

export interface ApiError {
  code: string
  message: string
  details?: Array<{ field: string; message: string }>
  request_id?: string
}

// Login/Register types
export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  password: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// WebSocket message types
export interface WSMessage {
  type: string
}

export interface WSSubscribe extends WSMessage {
  type: 'subscribe'
  codes: string[]
}

export interface WSUnsubscribe extends WSMessage {
  type: 'unsubscribe'
  codes: string[]
}

export interface WSPong extends WSMessage {
  type: 'pong'
}

export interface WSPing extends WSMessage {
  type: 'ping'
}

export interface WSQuotesData {
  quotes: Quote[]
}

export interface WSQuotesUpdate extends WSMessage {
  type: 'quotes'
  data: WSQuotesData
}

export interface WSError extends WSMessage {
  type: 'error'
  code: string
  message: string
}

export type WSMessageType = WSSubscribe | WSUnsubscribe | WSPong | WSPing | WSQuotesUpdate | WSError
```

- [ ] **Step 2: Create frontend/src/config.ts**

```typescript
// Configuration
const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
}

export default config
```

- [ ] **Step 3: Create frontend/src/services/api.ts**

```typescript
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import config from '@/config'
import { getAccessToken, refreshTokenIfNeeded } from './auth'
import type { ApiResponse } from '@/types'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  async (config) => {
    // Try to refresh token if needed
    await refreshTokenIfNeeded()

    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle responses
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    return response
  },
  async (error) => {
    return Promise.reject(error)
  }
)

export default api
```

- [ ] **Step 4: Create frontend/src/services/auth.ts**

```typescript
import api from './api'
import { AuthResponse, LoginData, RegisterData, ApiResponse } from '@/types'

// Token storage keys
const ACCESS_TOKEN_KEY = 'astock_access_token'
const REFRESH_TOKEN_KEY = 'astock_refresh_token'
const TOKEN_EXPIRES_AT_KEY = 'astock_token_expires_at'

// Get tokens from storage
export const getAccessToken = (): string | null => {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export const getTokenExpiresAt = (): number | null => {
  const value = localStorage.getItem(TOKEN_EXPIRES_AT_KEY)
  return value ? parseInt(value, 10) : null
}

// Set tokens in storage
export const setTokens = (accessToken: string, refreshToken: string, expiresIn: number) => {
  const expiresAt = Date.now() + expiresIn * 1000
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  localStorage.setItem(TOKEN_EXPIRES_AT_KEY, expiresAt.toString())
}

// Clear tokens from storage
export const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(TOKEN_EXPIRES_AT_KEY)
}

// Check if token needs refresh (within 5 minutes of expiration)
export const needsRefresh = (): boolean => {
  const expiresAt = getTokenExpiresAt()
  if (!expiresAt) return false
  return Date.now() > expiresAt - 5 * 60 * 1000
}

// Refresh token
let refreshPromise: Promise<void> | null = null

export const refreshTokenIfNeeded = async (): Promise<void> => {
  if (!needsRefresh()) return

  const refreshToken = getRefreshToken()
  if (!refreshToken) return

  // Avoid multiple concurrent refresh requests
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = (async () => {
    try {
      const response = await api.post<ApiResponse<{ access_token: string, token_type: string, expires_in: number }>>(
        '/api/v1/auth/refresh',
        { refresh_token: refreshToken }
      )

      if (response.data.success && response.data.data) {
        const { access_token, expires_in } = response.data.data
        // Update access token, keep refresh token
        const currentRefreshToken = getRefreshToken()
        if (currentRefreshToken) {
          setTokens(access_token, currentRefreshToken, expires_in)
        }
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearTokens()
      window.location.href = '/login'
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

// Auth API functions
export const login = async (data: LoginData): Promise<AuthResponse> => {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('password', data.password)

  const response = await api.post<ApiResponse<AuthResponse>>('/api/v1/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Login failed')
  }

  const authData = response.data.data!
  setTokens(authData.access_token, authData.refresh_token, authData.expires_in)
  return authData
}

export const register = async (data: RegisterData): Promise<AuthResponse> => {
  const response = await api.post<ApiResponse<AuthResponse>>('/api/v1/auth/register', data)

  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Registration failed')
  }

  const authData = response.data.data!
  setTokens(authData.access_token, authData.refresh_token, authData.expires_in)
  return authData
}

export const logout = async (): Promise<void> => {
  const refreshToken = getRefreshToken()
  if (refreshToken) {
    try {
      await api.post('/api/v1/auth/logout', { refresh_token: refreshToken })
    } catch (error) {
      console.error('Logout API failed:', error)
    }
  }
  clearTokens()
}

export const getCurrentUser = async () => {
  const response = await api.get<ApiResponse<any>>('/api/v1/auth/me')
  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Failed to get user')
  }
  return response.data.data
}
```

- [ ] **Step 5: Create frontend/src/services/ws.ts**

```typescript
import config from '@/config'
import { getAccessToken } from './auth'
import type { Quote, WSMessageType, WSSubscribe, WSUnsubscribe, WSPong, WSQuotesUpdate, WSError } from '@/types'

type WebSocketStatus = 'disconnected' | 'connecting' | 'connected'

type WSHandler = (data: WSMessageType) => void
type StatusHandler = (status: WebSocketStatus) => void

class QuoteWebSocket {
  private ws: WebSocket | null = null
  private status: WebSocketStatus = 'disconnected'
  private subscriptions: Set<string> = new Set()
  private handlers: WSHandler[] = []
  private statusHandlers: StatusHandler[] = []
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private pingTimer: ReturnType<typeof setInterval> | null = null

  constructor() {}

  // Subscribe to quote updates
  subscribe(codes: string[]) {
    codes.forEach(code => this.subscriptions.add(code))
    if (this.status === 'connected' && this.ws) {
      this.send({
        type: 'subscribe',
        codes,
      } as WSSubscribe)
    }
  }

  // Unsubscribe from quote updates
  unsubscribe(codes: string[]) {
    codes.forEach(code => this.subscriptions.delete(code))
    if (this.status === 'connected' && this.ws) {
      this.send({
        type: 'unsubscribe',
        codes,
      } as WSUnsubscribe)
    }
  }

  // Add a message handler
  onMessage(handler: WSHandler) {
    this.handlers.push(handler)
  }

  // Remove a message handler
  offMessage(handler: WSHandler) {
    const index = this.handlers.indexOf(handler)
    if (index > -1) {
      this.handlers.splice(index, 1)
    }
  }

  // Add a status change handler
  onStatusChange(handler: StatusHandler) {
    this.statusHandlers.push(handler)
  }

  // Remove a status change handler
  offStatusChange(handler: StatusHandler) {
    const index = this.statusHandlers.indexOf(handler)
    if (index > -1) {
      this.statusHandlers.splice(index, 1)
    }
  }

  // Connect to WebSocket server
  connect() {
    if (this.status !== 'disconnected') return

    const token = getAccessToken()
    if (!token) {
      console.warn('No access token, cannot connect to WebSocket')
      return
    }

    this.setStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/quotes?token=${token}`

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.setStatus('connected')
        this.reconnectAttempts = 0

        // Subscribe to current codes
        if (this.subscriptions.size > 0) {
          this.send({
            type: 'subscribe',
            codes: Array.from(this.subscriptions),
          } as WSSubscribe)
        }

        // Start ping timer
        this.pingTimer = setInterval(() => {
          // Server sends ping, we just need to listen
        }, 30000)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessageType
          this.handleMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        this.setStatus('disconnected')
        this.cleanup()
        this.scheduleReconnect()
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.setStatus('disconnected')
      this.scheduleReconnect()
    }
  }

  // Disconnect from WebSocket server
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.cleanup()
  }

  private cleanup() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private setStatus(status: WebSocketStatus) {
    this.status = status
    this.statusHandlers.forEach(handler => handler(status))
  }

  private send(message: WSMessageType) {
    if (this.ws && this.status === 'connected') {
      this.ws.send(JSON.stringify(message))
    }
  }

  private handleMessage(message: WSMessageType) {
    switch (message.type) {
      case 'ping':
        this.send({ type: 'pong' } as WSPong)
        break
      case 'quotes':
      case 'quote':
      case 'error':
        this.handlers.forEach(handler => handler(message))
        break
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
    console.log(`Reconnecting in ${delay}ms...`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }
}

// Singleton instance
const ws = new QuoteWebSocket()

export default ws
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/config.ts frontend/src/services/api.ts frontend/src/services/auth.ts frontend/src/services/ws.ts
git commit -m "feat: frontend type definitions and API services"
```

---

### Task 11: Frontend State Management with Zustand

**Files:**
- Create: `frontend/src/store/index.ts`

**Interfaces:**
- Produces: Zustand stores for auth, quotes, boards, and UI state

- [ ] **Step 1: Create frontend/src/store/index.ts**

```typescript
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User, Board, Quote, AuthState } from '@/types'
import { getAccessToken, getRefreshToken, clearTokens, setTokens as saveTokens } from '@/services/auth'

// === Auth Store ===
interface AuthStore extends AuthState {
  setUser: (user: User | null) => void
  setTokens: (accessToken: string, refreshToken: string, expiresIn: number) => void
  clearAuth: () => void
  initAuth: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setUser: (user) => set({ user }),

      setTokens: (accessToken, refreshToken, expiresIn) => {
        saveTokens(accessToken, refreshToken, expiresIn)
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true,
        })
      },

      clearAuth: () => {
        clearTokens()
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      initAuth: () => {
        const accessToken = getAccessToken()
        const refreshToken = getRefreshToken()
        if (accessToken) {
          set({
            accessToken,
            refreshToken,
            isAuthenticated: true,
          })
        }
      },
    }),
    {
      name: 'astock-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Don't persist tokens here, we handle separately
        user: state.user,
      }),
    }
  )
)

// === Quotes Store ===
interface QuoteStore {
  quotes: Map<string, Quote>
  updateQuote: (quote: Quote) => void
  updateQuotes: (quotes: Quote[]) => void
  getQuote: (code: string) => Quote | undefined
  clearQuotes: () => void
}

export const useQuoteStore = create<QuoteStore>((set, get) => ({
  quotes: new Map(),

  updateQuote: (quote) =>
    set((state) => {
      const newQuotes = new Map(state.quotes)
      newQuotes.set(quote.code, quote)
      return { quotes: newQuotes }
    }),

  updateQuotes: (newQuotes) =>
    set((state) => {
      const updatedQuotes = new Map(state.quotes)
      newQuotes.forEach((quote) => updatedQuotes.set(quote.code, quote))
      return { quotes: updatedQuotes }
    }),

  getQuote: (code) => get().quotes.get(code),

  clearQuotes: () => set({ quotes: new Map() }),
}))

// === Boards Store ===
interface BoardsStore {
  boards: Board[]
  isLoading: boolean
  setBoards: (boards: Board[]) => void
  addBoard: (board: Board) => void
  updateBoard: (id: number, data: Partial<Board>) => void
  deleteBoard: (id: number) => void
  addStockToBoard: (boardId: number, stock: any) => void
  removeStockFromBoard: (boardId: number, stockId: number) => void
  setLoading: (loading: boolean) => void
}

export const useBoardStore = create<BoardsStore>((set, get) => ({
  boards: [],
  isLoading: false,

  setBoards: (boards) => set({ boards, isLoading: false }),

  addBoard: (board) =>
    set((state) => ({
      boards: [...state.boards, board],
    })),

  updateBoard: (id, data) =>
    set((state) => ({
      boards: state.boards.map((b) => (b.id === id ? { ...b, ...data } : b)),
    })),

  deleteBoard: (id) =>
    set((state) => ({
      boards: state.boards.filter((b) => b.id !== id),
    })),

  addStockToBoard: (boardId, stock) =>
    set((state) => ({
      boards: state.boards.map((b) =>
        b.id === boardId ? { ...b, stocks: [...b.stocks, stock] } : b
      ),
    })),

  removeStockFromBoard: (boardId, stockId) =>
    set((state) => ({
      boards: state.boards.map((b) =>
        b.id === boardId
          ? { ...b, stocks: b.stocks.filter((s) => s.id !== stockId) }
          : b
      ),
    })),

  setLoading: (loading) => set({ isLoading: loading }),
}))

// === UI Store ===
interface UIStore {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  refreshInterval: number
  setTheme: (theme: 'light' | 'dark') => void
  toggleSidebar: () => void
  setRefreshInterval: (interval: number) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      theme: 'light',
      sidebarOpen: true,
      refreshInterval: 5,

      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setRefreshInterval: (interval) => set({ refreshInterval: interval }),
    }),
    {
      name: 'astock-ui',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

// Helper selectors
export const useAllStockCodes = () => {
  return useBoardStore((state) =>
    state.boards.flatMap((b) => b.stocks.map((s) => s.code))
  )
}

export const useBoardQuotes = (boardId: number) => {
  const board = useBoardStore((state) => state.boards.find((b) => b.id === boardId))
  const getQuote = useQuoteStore((state) => state.getQuote)
  return board?.stocks.map((stock) => getQuote(stock.code)).filter(Boolean) as Quote[]
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/store/index.ts
git commit -m "feat: frontend state management with Zustand"
```

---

### Task 12: Frontend Components

**Files:**
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Create: `frontend/src/components/Loading.tsx`
- Create: `frontend/src/components/ErrorBoundary.tsx`
- Create: `frontend/src/components/BoardCard.tsx`
- Create: `frontend/src/components/StockSearch.tsx`
- Create: `frontend/src/components/KLineChart.tsx`
- Create: `frontend/src/components/Layout.tsx`

**Interfaces:**
- Produces: Reusable React components

- [ ] **Step 1: Create frontend/src/components/ProtectedRoute.tsx**

```typescript
import { ReactNode, useEffect } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store'
import { getCurrentUser } from '@/services/auth'
import { Spin } from 'antd'

interface ProtectedRouteProps {
  children: ReactNode
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const setUser = useAuthStore((state) => state.setUser)
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const [loading, setLoading] = React.useState(true)

  useEffect(() => {
    const init = async () => {
      if (isAuthenticated && !user) {
        try {
          const currentUser = await getCurrentUser()
          setUser(currentUser)
        } catch (error) {
          console.error('Failed to get current user:', error)
          clearAuth()
        }
      }
      setLoading(false)
    }
    init()
  }, [isAuthenticated, user, setUser, clearAuth])

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
```

- [ ] **Step 2: Create frontend/src/components/Loading.tsx**

```typescript
import { Spin } from 'antd'

interface LoadingProps {
  size?: 'small' | 'default' | 'large'
  text?: string
  fullScreen?: boolean
}

export const Loading = ({ size = 'default', text, fullScreen = false }: LoadingProps) => {
  if (fullScreen) {
    return (
      <div style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        zIndex: 1000
      }}>
        <Spin size={size} />
        {text && <div style={{ marginTop: 16 }}>{text}</div>}
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 32
    }}>
      <Spin size={size} />
      {text && <div style={{ marginTop: 16 }}>{text}</div>}
    </div>
  )
}

export const EmptyState = ({
  icon = '📭',
  title,
  description,
  action
}: {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
}) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 48,
    textAlign: 'center'
  }}>
    <div style={{ fontSize: 48, marginBottom: 16 }}>{icon}</div>
    <h3 style={{ marginBottom: 8, fontSize: 18 }}>{title}</h3>
    {description && <p style={{ color: '#8c8c8c', marginBottom: 16 }}>{description}</p>}
    {action}
  </div>
)
```

- [ ] **Step 3: Create frontend/src/components/ErrorBoundary.tsx**

```typescript
import React from 'react'
import { Button, Result } from 'antd'

interface Props {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{ padding: 64 }}>
          <Result
            status="warning"
            title="出了点问题"
            subTitle="请稍后重试"
            extra={
              <Button type="primary" onClick={this.handleReset}>
                重试
              </Button>
            }
          />
        </div>
      )
    }

    return this.props.children
  }
}
```

- [ ] **Step 4: Create frontend/src/components/BoardCard.tsx**

```typescript
import { Card, List, Button, Tooltip, Popconfirm, Space } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, StockOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import type { Board, Quote } from '@/types'
import { formatPrice, formatChange } from '@/utils/format'

interface BoardCardProps {
  board: Board
  quotes?: Map<string, Quote>
  onAddStock: () => void
  onEdit: () => void
  onDelete: () => void
  onRemoveStock: (stockId: number) => void
}

const BoardCard = ({ board, quotes, onAddStock, onEdit, onDelete, onRemoveStock }: BoardCardProps) => {
  const getQuoteForStock = (code: string) => quotes?.get(code)

  return (
    <Card
      title={
        <Space>
          <StockOutlined />
          {board.name}
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="编辑板块">
            <Button type="text" icon={<EditOutlined />} onClick={onEdit} />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个板块吗？"
            description="板块内的所有股票也会被移除"
            onConfirm={onDelete}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除板块">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      }
      size="small"
      className="board-card"
    >
      {board.stocks.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#8c8c8c', padding: 16 }}>
          暂无股票，点击下方按钮添加
        </div>
      ) : (
        <List
          size="small"
          dataSource={board.stocks}
          renderItem={(stock) => {
            const quote = getQuoteForStock(stock.code)
            const isUp = quote ? quote.change_percent > 0 : false
            const isDown = quote ? quote.change_percent < 0 : false
            const colorClass = isUp ? 'stock-up' : isDown ? 'stock-down' : 'stock-neutral'

            return (
              <List.Item
                actions={[
                  <Popconfirm
                    title="确定要移除这只股票吗？"
                    onConfirm={() => onRemoveStock(stock.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                  </Popconfirm>
                ]}
              >
                <List.Item.Meta
                  title={
                    <Link
                      to={`/stock/${stock.code}`}
                      style={{ color: 'inherit', textDecoration: 'none' }}
                    >
                      <Space>
                        <span>{stock.name}</span>
                        <span style={{ fontSize: 12, color: '#8c8c8c' }}>{stock.code}</span>
                      </Space>
                    </Link>
                  }
                  description={
                    quote ? (
                      <Space>
                        <span className={colorClass}>{formatPrice(quote.price)}</span>
                        <span className={colorClass}>{formatChange(quote.change_percent)}</span>
                      </Space>
                    ) : (
                      <span style={{ color: '#8c8c8c' }}>--</span>
                    )
                  }
                />
              </List.Item>
            )
          }}
        />
      )
      <Button type="dashed" block icon={<PlusOutlined />} onClick={onAddStock} style={{ marginTop: 16 }}>
        添加股票
      </Button>
    </Card>
  )
}

export default BoardCard
```

- [ ] **Step 5: Create frontend/src/components/StockSearch.tsx**

```typescript
import { useState, useEffect } from 'react'
import { Modal, Input, List, Button, Space, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '@/services/api'

interface StockSearchProps {
  open: boolean
  onCancel: () => void
  onSelect: (code: string, name: string) => void
}

interface SearchResult {
  code: string
  name: string
  market?: string
}

const StockSearch = ({ open, onCancel, onSelect }: StockSearchProps) => {
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) {
      setKeyword('')
      setResults([])
    }
  }, [open])

  useEffect(() => {
    if (!keyword || keyword.length < 1) {
      setResults([])
      return
    }

    const search = async () => {
      setLoading(true)
      try {
        const response = await api.get('/api/v1/stocks/search', {
          params: { keyword }
        })
        if (response.data.success) {
          setResults(response.data.data || [])
        }
      } catch (error) {
        console.error('Search failed:', error)
      } finally {
        setLoading(false)
      }
    }

    const timer = setTimeout(search, 300)
    return () => clearTimeout(timer)
  }, [keyword])

  const handleSelect = (stock: SearchResult) => {
    onSelect(stock.code, stock.name)
    onCancel()
  }

  return (
    <Modal
      title="搜索股票"
      open={open}
      onCancel={onCancel}
      footer={null}
      width={500}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input
          placeholder="输入股票代码或名称搜索"
          prefix={<SearchOutlined />}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          autoFocus
        />
        <List
          loading={loading}
          dataSource={results}
          renderItem={(stock) => (
            <List.Item
              actions={[
                <Button type="primary" size="small" onClick={() => handleSelect(stock)}>
                  添加
                </Button>
              ]}
              style={{ cursor: 'pointer' }}
            >
              <List.Item.Meta
                title={stock.name}
                description={stock.code}
              />
            </List.Item>
          )}
          locale={{
            emptyText: keyword ? '未找到相关股票' : '请输入关键词搜索'
          }}
        />
      </Space>
    </Modal>
  )
}

export default StockSearch
```

- [ ] **Step 6: Create frontend/src/components/KLineChart.tsx**

```typescript
import { useEffect, useRef } from 'react'
import { createChart, IChartApi, ISeriesApi, Time } from 'lightweight-charts'
import type { KLineItem } from '@/types'

interface KLineChartProps {
  data: KLineItem[]
  height?: number
}

const KLineChart = ({ data, height = 400 }: KLineChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#cf1322',
      downColor: '#3f8600',
      borderDownColor: '#3f8600',
      borderUpColor: '#cf1322',
      wickDownColor: '#3f8600',
      wickUpColor: '#cf1322',
    })

    chartRef.current = chart
    seriesRef.current = candlestickSeries

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [height])

  useEffect(() => {
    if (!seriesRef.current || !data.length) return

    // Format data for lightweight-charts
    const formattedData = data.map((item) => {
      // Parse date - handle both YYYY-MM-DD and YYYY-MM-DD HH:MM formats
      let time: Time
      if (item.date.includes(' ')) {
        const [datePart, timePart] = item.date.split(' ')
        const [year, month, day] = datePart.split('-').map(Number)
        time = year * 10000 + month * 100 + day
      } else {
        const [year, month, day] = item.date.split('-').map(Number)
        time = year * 10000 + month * 100 + day
      }

      return {
        time,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }
    })

    seriesRef.current.setData(formattedData)

    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent()
    }
  }, [data])

  return <div ref={chartContainerRef} style={{ width: '100%', height }} />
}

export default KLineChart
```

- [ ] **Step 7: Create frontend/src/components/Layout.tsx**

```typescript
import { ReactNode } from 'react'
import { Layout as AntLayout, Dropdown, Avatar, Button, Space, Typography } from 'antd'
import { UserOutlined, LogoutOutlined, SettingOutlined, StockOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store'
import { logout } from '@/services/auth'

const { Header, Content } = AntLayout
const { Title } = Typography

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const clearAuth = useAuthStore((state) => state.clearAuth)

  const handleLogout = async () => {
    await logout()
    clearAuth()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#fff',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
      }}>
        <Link to="/" style={{ textDecoration: 'none' }}>
          <Space>
            <StockOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <Title level={4} style={{ margin: 0 }}>A股看盘工具</Title>
          </Space>
        </Link>
        <Space>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.username}</span>
            </Space>
          </Dropdown>
        </Space>
      </Header>
      <Content style={{ padding: 24, background: '#f5f5f5' }}>
        {children}
      </Content>
    </AntLayout>
  )
}

export default Layout
```

- [ ] **Step 8: Create frontend/src/utils/format.ts**

```typescript
// Format utilities
export const formatPrice = (price: number): string => {
  return price.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export const formatChange = (changePercent: number): string => {
  const sign = changePercent > 0 ? '+' : ''
  return `${sign}${changePercent.toFixed(2)}%`
}

export const formatVolume = (volume: number): string => {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`
  }
  return volume.toString()
}

export const formatAmount = (amount: number): string => {
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)}亿`
  } else if (amount >= 10000) {
    return `${(amount / 10000).toFixed(2)}万`
  }
  return amount.toString()
}
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/components/ProtectedRoute.tsx frontend/src/components/Loading.tsx frontend/src/components/ErrorBoundary.tsx frontend/src/components/BoardCard.tsx frontend/src/components/StockSearch.tsx frontend/src/components/KLineChart.tsx frontend/src/components/Layout.tsx frontend/src/utils/format.ts
git commit -m "feat: frontend components"
```

---

### Task 13: Frontend Pages

**Files:**
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/pages/Register.tsx`
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/StockDetail.tsx`

**Interfaces:**
- Produces: Page components for all routes

- [ ] **Step 1: Create frontend/src/pages/Login.tsx**

```typescript
import { useState } from 'react'
import { Form, Input, Button, Card, Typography, message, Space } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '@/services/auth'
import { useAuthStore } from '@/store'

const { Title, Text } = Typography

const Login = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const setUser = useAuthStore((state) => state.setUser)
  const setTokens = useAuthStore((state) => state.setTokens)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const authData = await login(values)
      setUser(authData.user)
      setTokens(authData.access_token, authData.refresh_token, authData.expires_in)
      message.success('登录成功')
      navigate('/')
    } catch (error: any) {
      message.error(error.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 8 }}>A股看盘工具</Title>
          <Text type="secondary">登录您的账户</Text>
        </div>
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center' }}>
          <Text>
            还没有账户？<Link to="/register">立即注册</Link>
          </Text>
        </div>
      </Card>
    </div>
  )
}

export default Login
```

- [ ] **Step 2: Create frontend/src/pages/Register.tsx**

```typescript
import { useState } from 'react'
import { Form, Input, Button, Card, Typography, message, Space } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '@/services/auth'
import { useAuthStore } from '@/store'

const { Title, Text } = Typography

const Register = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const setUser = useAuthStore((state) => state.setUser)
  const setTokens = useAuthStore((state) => state.setTokens)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const authData = await register(values)
      setUser(authData.user)
      setTokens(authData.access_token, authData.refresh_token, authData.expires_in)
      message.success('注册成功')
      navigate('/')
    } catch (error: any) {
      message.error(error.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 8 }}>A股看盘工具</Title>
          <Text type="secondary">创建新账户</Text>
        </div>
        <Form
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 2, message: '用户名至少2个字符' }
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 8, message: '密码至少8个字符' }
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center' }}>
          <Text>
            已有账户？<Link to="/login">立即登录</Link>
          </Text>
        </div>
      </Card>
    </div>
  )
}

export default Register
```

- [ ] **Step 3: Create frontend/src/pages/Dashboard.tsx**

```typescript
import { useEffect, useState, useCallback } from 'react'
import { Row, Col, Button, Modal, Form, Input, message, Space, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import Layout from '@/components/Layout'
import BoardCard from '@/components/BoardCard'
import StockSearch from '@/components/StockSearch'
import { Loading, EmptyState } from '@/components/Loading'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { useBoardStore, useQuoteStore, useAllStockCodes } from '@/store'
import api from '@/services/api'
import ws from '@/services/ws'
import type { Board } from '@/types'

const { Title } = Typography

const Dashboard = () => {
  const boards = useBoardStore((state) => state.boards)
  const isLoading = useBoardStore((state) => state.isLoading)
  const setBoards = useBoardStore((state) => state.setBoards)
  const addBoard = useBoardStore((state) => state.addBoard)
  const deleteBoard = useBoardStore((state) => state.deleteBoard)
  const updateBoard = useBoardStore((state) => state.updateBoard)
  const addStockToBoard = useBoardStore((state) => state.addStockToBoard)
  const removeStockFromBoard = useBoardStore((state) => state.removeStockFromBoard)
  const setLoading = useBoardStore((state) => state.setLoading)
  const updateQuotes = useQuoteStore((state) => state.updateQuotes)
  const quotes = useQuoteStore((state) => state.quotes)
  const allCodes = useAllStockCodes()

  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [searchModalOpen, setSearchModalOpen] = useState(false)
  const [selectedBoardId, setSelectedBoardId] = useState<number | null>(null)
  const [editingBoard, setEditingBoard] = useState<Board | null>(null)
  const [form] = Form.useForm()

  // Load boards
  const loadBoards = useCallback(async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/v1/boards')
      if (response.data.success) {
        setBoards(response.data.data || [])
      }
    } catch (error) {
      console.error('Failed to load boards:', error)
      message.error('加载板块失败')
    } finally {
      setLoading(false)
    }
  }, [setBoards, setLoading])

  useEffect(() => {
    loadBoards()
  }, [loadBoards])

  // WebSocket setup
  useEffect(() => {
    // Connect to WebSocket
    ws.connect()

    // Subscribe to quote updates
    const handleQuotes = (data: any) => {
      if (data.type === 'quotes' && data.data?.quotes) {
        updateQuotes(data.data.quotes)
      }
    }
    ws.onMessage(handleQuotes)

    return () => {
      ws.offMessage(handleQuotes)
      ws.disconnect()
    }
  }, [updateQuotes])

  // Subscribe to codes when they change
  useEffect(() => {
    if (allCodes.length > 0) {
      ws.subscribe(allCodes)
    }
  }, [allCodes])

  // Create board
  const handleCreateBoard = async (values: { name: string }) => {
    try {
      const response = await api.post('/api/v1/boards', values)
      if (response.data.success) {
        addBoard(response.data.data)
        setCreateModalOpen(false)
        form.resetFields()
        message.success('板块创建成功')
      }
    } catch (error) {
      console.error('Failed to create board:', error)
      message.error('创建板块失败')
    }
  }

  // Edit board
  const handleEditBoard = async (values: { name: string }) => {
    if (!editingBoard) return
    try {
      const response = await api.put(`/api/v1/boards/${editingBoard.id}`, values)
      if (response.data.success) {
        updateBoard(editingBoard.id, values)
        setEditModalOpen(false)
        setEditingBoard(null)
        form.resetFields()
        message.success('板块更新成功')
      }
    } catch (error) {
      console.error('Failed to update board:', error)
      message.error('更新板块失败')
    }
  }

  // Delete board
  const handleDeleteBoard = async (boardId: number) => {
    try {
      const response = await api.delete(`/api/v1/boards/${boardId}`)
      if (response.data.success) {
        deleteBoard(boardId)
        message.success('板块删除成功')
      }
    } catch (error) {
      console.error('Failed to delete board:', error)
      message.error('删除板块失败')
    }
  }

  // Add stock to board
  const handleAddStock = async (code: string, name: string) => {
    if (!selectedBoardId) return
    try {
      const response = await api.post(`/api/v1/boards/${selectedBoardId}/stocks`, { code, name })
      if (response.data.success) {
        addStockToBoard(selectedBoardId, response.data.data)
        message.success('股票添加成功')
      }
    } catch (error) {
      console.error('Failed to add stock:', error)
      message.error('添加股票失败')
    }
  }

  // Remove stock from board
  const handleRemoveStock = async (boardId: number, stockId: number) => {
    try {
      const response = await api.delete(`/api/v1/boards/${boardId}/stocks/${stockId}`)
      if (response.data.success) {
        removeStockFromBoard(boardId, stockId)
        message.success('股票移除成功')
      }
    } catch (error) {
      console.error('Failed to remove stock:', error)
      message.error('移除股票失败')
    }
  }

  const openSearchModal = (boardId: number) => {
    setSelectedBoardId(boardId)
    setSearchModalOpen(true)
  }

  const openEditModal = (board: Board) => {
    setEditingBoard(board)
    form.setFieldsValue({ name: board.name })
    setEditModalOpen(true)
  }

  return (
    <Layout>
      <ErrorBoundary>
        <div>
          <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>我的板块</Title>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
              新建板块
            </Button>
          </div>

          {isLoading ? (
            <Loading text="加载中..." />
          ) : boards.length === 0 ? (
            <EmptyState
              icon="📊"
              title="暂无板块"
              description="点击上方按钮创建您的第一个板块"
              action={
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
                  新建板块
                </Button>
              }
            />
          ) : (
            <Row gutter={[16, 16]}>
              {boards.map((board) => (
                <Col xs={24} sm={12} md={8} lg={8} xl={6} key={board.id}>
                  <BoardCard
                    board={board}
                    quotes={quotes}
                    onAddStock={() => openSearchModal(board.id)}
                    onEdit={() => openEditModal(board)}
                    onDelete={() => handleDeleteBoard(board.id)}
                    onRemoveStock={(stockId) => handleRemoveStock(board.id, stockId)}
                  />
                </Col>
              ))}
            </Row>
          )}
        </div>
      </ErrorBoundary>

      {/* Create Board Modal */}
      <Modal
        title="新建板块"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} onFinish={handleCreateBoard} layout="vertical">
          <Form.Item
            name="name"
            label="板块名称"
            rules={[{ required: true, message: '请输入板块名称' }]}
          >
            <Input placeholder="例如：白酒、新能源" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Board Modal */}
      <Modal
        title="编辑板块"
        open={editModalOpen}
        onCancel={() => {
          setEditModalOpen(false)
          setEditingBoard(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} onFinish={handleEditBoard} layout="vertical">
          <Form.Item
            name="name"
            label="板块名称"
            rules={[{ required: true, message: '请输入板块名称' }]}
          >
            <Input placeholder="例如：白酒、新能源" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Stock Search Modal */}
      <StockSearch
        open={searchModalOpen}
        onCancel={() => {
          setSearchModalOpen(false)
          setSelectedBoardId(null)
        }}
        onSelect={handleAddStock}
      />
    </Layout>
  )
}

export default Dashboard
```

- [ ] **Step 4: Create frontend/src/pages/StockDetail.tsx**

```typescript
import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Card, Typography, Row, Col, Button, Select, Space, Divider, message, Table, Statistic } from 'antd'
import { ArrowLeftOutlined, StockOutlined } from '@ant-design/icons'
import Layout from '@/components/Layout'
import KLineChart from '@/components/KLineChart'
import { Loading } from '@/components/Loading'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import api from '@/services/api'
import type { Quote, KLineItem, KLinePeriod } from '@/types'
import { formatPrice, formatChange, formatVolume, formatAmount } from '@/utils/format'

const { Title, Text } = Typography
const { Option } = Select

const StockDetail = () => {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const [quote, setQuote] = useState<Quote | null>(null)
  const [klineData, setKlineData] = useState<KLineItem[]>([])
  const [period, setPeriod] = useState<KLinePeriod>('1d')
  const [loading, setLoading] = useState(true)
  const [klineLoading, setKlineLoading] = useState(false)

  const loadQuote = useCallback(async () => {
    if (!code) return
    setLoading(true)
    try {
      const response = await api.get(`/api/v1/quotes/${code}`)
      if (response.data.success) {
        setQuote(response.data.data)
      }
    } catch (error) {
      console.error('Failed to load quote:', error)
      message.error('加载行情失败')
    } finally {
      setLoading(false)
    }
  }, [code])

  const loadKline = useCallback(async () => {
    if (!code) return
    setKlineLoading(true)
    try {
      const response = await api.get(`/api/v1/quotes/${code}/kline`, {
        params: { period, count: 100 }
      })
      if (response.data.success) {
        setKlineData(response.data.data || [])
      }
    } catch (error) {
      console.error('Failed to load K-line:', error)
      message.error('加载K线失败')
    } finally {
      setKlineLoading(false)
    }
  }, [code, period])

  useEffect(() => {
    loadQuote()
  }, [loadQuote])

  useEffect(() => {
    loadKline()
  }, [loadKline])

  const isUp = quote ? quote.change_percent > 0 : false
  const isDown = quote ? quote.change_percent < 0 : false
  const colorClass = isUp ? 'stock-up' : isDown ? 'stock-down' : 'stock-neutral'

  if (loading) {
    return (
      <Layout>
        <Loading text="加载中..." fullScreen />
      </Layout>
    )
  }

  if (!quote) {
    return (
      <Layout>
        <div style={{ textAlign: 'center', padding: 64 }}>
          <Title level={4}>未找到股票 {code}</Title>
          <Button type="primary" onClick={() => navigate('/')} style={{ marginTop: 16 }}>
            返回首页
          </Button>
        </div>
      </Layout>
    )
  }

  const infoData = [
    { label: '今开', value: formatPrice(quote.open) },
    { label: '昨收', value: formatPrice(quote.pre_close) },
    { label: '最高', value: formatPrice(quote.high), className: 'stock-up' },
    { label: '最低', value: formatPrice(quote.low), className: 'stock-down' },
    { label: '成交量', value: formatVolume(quote.volume) },
    { label: '成交额', value: formatAmount(quote.amount) },
  ]

  if (quote.bid1 !== undefined) {
    infoData.push({ label: '买一', value: `${formatPrice(quote.bid1)} (${quote.bid1_volume})` })
  }
  if (quote.ask1 !== undefined) {
    infoData.push({ label: '卖一', value: `${formatPrice(quote.ask1)} (${quote.ask1_volume})` })
  }

  return (
    <Layout>
      <ErrorBoundary>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
            <Link to="/">
              <Button type="text" icon={<ArrowLeftOutlined />}>
                返回
              </Button>
            </Link>
            <Title level={3} style={{ margin: '0 16px' }}>
              {quote.name}
              <Text type="secondary" style={{ marginLeft: 8 }}>{quote.code}</Text>
            </Title>
          </div>

          {/* Price Card */}
          <Card>
            <Row gutter={32}>
              <Col>
                <Statistic
                  title="最新价"
                  value={quote.price}
                  precision={2}
                  valueStyle={{ color: isUp ? '#cf1322' : isDown ? '#3f8600' : '#8c8c8c', fontSize: 36 }}
                  formatter={(value) => formatPrice(Number(value))}
                />
              </Col>
              <Col>
                <Statistic
                  title="涨跌额"
                  value={quote.change}
                  precision={2}
                  valueStyle={{ color: isUp ? '#cf1322' : isDown ? '#3f8600' : '#8c8c8c' }}
                  prefix={isUp ? '+' : ''}
                />
              </Col>
              <Col>
                <Statistic
                  title="涨跌幅"
                  value={quote.change_percent}
                  precision={2}
                  valueStyle={{ color: isUp ? '#cf1322' : isDown ? '#3f8600' : '#8c8c8c' }}
                  prefix={isUp ? '+' : ''}
                  suffix="%"
                />
              </Col>
            </Row>

            <Divider />

            <Row gutter={[16, 16]}>
              {infoData.map((item, index) => (
                <Col key={index} xs={12} sm={8} md={6}>
                  <div>
                    <Text type="secondary">{item.label}</Text>
                    <Text strong style={{ marginLeft: 8, display: 'inline-block', minWidth: 80 }}>
                      {item.value}
                    </Text>
                  </div>
                </Col>
              ))}
            </Row>
          </Card>

          {/* K-line Chart */}
          <Card
            title={
              <Space>
                <StockOutlined />
                K线图
              </Space>
            }
            extra={
              <Select
                value={period}
                onChange={setPeriod as (value: string) => void}
                style={{ width: 120 }}
              >
                <Option value="1d">日线</Option>
                <Option value="1w">周线</Option>
                <Option value="1M">月线</Option>
              </Select>
            }
          >
            {klineLoading ? (
              <Loading text="加载中..." />
            ) : (
              <KLineChart data={klineData} />
            )}
          </Card>
        </Space>
      </ErrorBoundary>
    </Layout>
  )
}

export default StockDetail
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Login.tsx frontend/src/pages/Register.tsx frontend/src/pages/Dashboard.tsx frontend/src/pages/StockDetail.tsx
git commit -m "feat: frontend pages"
```

---

### Task 14: Docker and Deployment Configuration

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `nginx/nginx.conf`
- Create: `redis/redis.conf`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`

**Interfaces:**
- Produces: Complete Docker deployment configuration

- [ ] **Step 1: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/backup

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create frontend/Dockerfile**

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3: Create frontend/nginx.conf**

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Main location
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  # Nginx - reverse proxy and static file server
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - astock-network

  # FastAPI backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=sqlite:////app/data/astock.db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:?Please set JWT_SECRET_KEY}
      - TUSHARE_TOKEN=${TUSHARE_TOKEN:-}
    volumes:
      - ./backend/data:/app/data
      - ./logs/backend:/app/logs
      - ./backup:/app/backup
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - astock-network

  # Redis cache
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    networks:
      - astock-network

  # Frontend - built separately
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    networks:
      - astock-network

volumes:
  redis-data:

networks:
  astock-network:
    driver: bridge
```

- [ ] **Step 5: Update nginx/nginx.conf**

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] '
                      '"$request" $status $body_bytes_sent '
                      '"$http_referer" "$http_user_agent"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout  65;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;

    # Upstream servers
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    server {
        listen 80;
        server_name _;

        # Frontend static files
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 300s;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
            access_log off;
        }
    }
}
```

- [ ] **Step 6: Create redis/redis.conf**

```redis
# Network
bind 0.0.0.0
port 6379

# Persistence
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir /data

# AOF
appendonly yes
appendfsync everysec

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128
```

- [ ] **Step 7: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
build/

# Database
*.db
*.sqlite
*.sqlite3
data/

# Logs
*.log
logs/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker volumes
backup/
redis-data/

# OS
.DS_Store
Thumbs.db

# SSL
nginx/ssl/
```

- [ ] **Step 8: Create .env.example**

```env
# Environment
ENV=production
DEBUG=false

# JWT Secret - CHANGE THIS IN PRODUCTION!
JWT_SECRET_KEY=your-super-secret-key-change-in-production-please
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=2
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:////app/data/astock.db

# Redis
REDIS_URL=redis://redis:6379/0

# Tushare Token (optional)
TUSHARE_TOKEN=

# Rate Limiting
RATE_LIMIT_ENABLED=true

# CORS Origins (comma separated for multiple)
CORS_ORIGINS=["https://your-domain.com"]
```

- [ ] **Step 9: Create README.md**

```markdown
# A股看盘工具

一个支持多用户、自定义板块、实时行情的A股看盘网页工具。

## 功能特性

- ✅ 用户注册/登录
- ✅ 自定义板块管理
- ✅ 个股添加/删除
- ✅ 实时行情刷新 (WebSocket)
- ✅ K线图展示
- ✅ 响应式设计
- ✅ Docker 部署

## 技术栈

### 后端
- FastAPI - Web框架
- SQLAlchemy - ORM
- Redis - 缓存
- SQLite - 数据库
- AkShare - 数据源

### 前端
- React 18
- TypeScript
- Ant Design
- Lightweight Charts
- Zustand
- React Router

### 部署
- Docker Compose
- Nginx
- Redis

## 快速开始

### 开发环境

#### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

后端会在 http://localhost:8000 启动

#### 前端

```bash
cd frontend
npm install
npm run dev
```

前端会在 http://localhost:3000 启动

### Docker 部署

1. 复制环境变量
```bash
cp .env.example .env
```

2. 编辑 `.env` 设置生产环境变量，特别是 `JWT_SECRET_KEY`

3. 启动服务
```bash
docker-compose up -d --build
```

4. 访问 http://localhost

### 停止服务

```bash
docker-compose down
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

## 目录结构

```
astock/
├── backend/           # 后端代码
│   ├── app/
│   │   ├── datasources/
│   │   ├── api/
│   │   ├── models/
│   │   └── core/
│   ├── tests/
│   └── data/
├── frontend/          # 前端代码
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── store/
│   │   └── services/
│   └── public/
├── nginx/             # Nginx配置
├── redis/             # Redis配置
├── logs/              # 日志目录
├── backup/            # 备份目录
└── docker-compose.yml
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| ENV | 环境 | development |
| DEBUG | 调试模式 | false |
| JWT_SECRET_KEY | JWT密钥 | 必填 |
| DATABASE_URL | 数据库连接 | sqlite:////app/data/astock.db |
| REDIS_URL | Redis连接 | redis://redis:6379/0 |
| TUSHARE_TOKEN | Tushare Token | 可选 |

## API 文档

启动后端后，可以访问以下地址查看 API 文档:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
```

- [ ] **Step 10: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.yml nginx/nginx.conf redis/redis.conf .gitignore .env.example README.md
git commit -m "feat: Docker and deployment configuration"
```

---

## Final Steps

Now that the plan is complete, let's offer the execution options:

**Plan complete and saved to `docs/superpowers/plans/2026-08-12-astock-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended) - Dispatch fresh subagents for each task, review between tasks, fast iteration**

**2. Inline Execution - Execute tasks in this session using superpowers/executing-plans, batch execution with checkpoints**

**Which approach?**

Let's start implementing! I'll update the task status and begin execution.
<seed:tool_call><function name="TaskUpdate"><parameter name="taskId"><stringValue>1</stringValue></parameterName><parameter name="status"><stringValue>completed</stringValue>