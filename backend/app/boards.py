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
