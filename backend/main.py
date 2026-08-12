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
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
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
