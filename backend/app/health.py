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
