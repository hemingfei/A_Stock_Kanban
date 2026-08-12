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
