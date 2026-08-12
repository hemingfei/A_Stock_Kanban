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
