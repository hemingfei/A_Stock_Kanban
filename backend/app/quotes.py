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
from .schemas import ApiResponse, Quote as QuoteSchema, KLineItem as KLineItemSchema
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

    async def broadcast_quotes(self, quotes: Dict[str, QuoteSchema]):
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
