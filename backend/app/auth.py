from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
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

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Token blacklist (in Redis in production, in-memory for dev)
token_blacklist: Dict[str, float] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


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
