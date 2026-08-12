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
