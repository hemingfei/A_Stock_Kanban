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
    "601318": Quote(
        code="601318",
        name="中国平安",
        price=45.00,
        pre_close=44.50,
        open=44.60,
        high=45.20,
        low=44.30,
        volume=1200000,
        amount=54000000,
        change=0.50,
        change_percent=1.12,
        bid1=44.99,
        bid1_volume=2000,
        ask1=45.01,
        ask1_volume=2000,
        timestamp=time.time()
    ),
    "000333": Quote(
        code="000333",
        name="美的集团",
        price=58.00,
        pre_close=57.50,
        open=57.60,
        high=58.50,
        low=57.20,
        volume=600000,
        amount=34800000,
        change=0.50,
        change_percent=0.87,
        bid1=57.99,
        bid1_volume=500,
        ask1=58.01,
        ask1_volume=500,
        timestamp=time.time()
    ),
    "600036": Quote(
        code="600036",
        name="招商银行",
        price=32.00,
        pre_close=31.80,
        open=31.90,
        high=32.30,
        low=31.70,
        volume=900000,
        amount=28800000,
        change=0.20,
        change_percent=0.63,
        bid1=31.99,
        bid1_volume=1500,
        ask1=32.01,
        ask1_volume=1500,
        timestamp=time.time()
    ),
    "002594": Quote(
        code="002594",
        name="比亚迪",
        price=240.00,
        pre_close=238.00,
        open=239.00,
        high=242.00,
        low=237.00,
        volume=400000,
        amount=96000000,
        change=2.00,
        change_percent=0.84,
        bid1=239.99,
        bid1_volume=300,
        ask1=240.01,
        ask1_volume=300,
        timestamp=time.time()
    ),
    "600900": Quote(
        code="600900",
        name="长江电力",
        price=28.00,
        pre_close=27.80,
        open=27.90,
        high=28.20,
        low=27.70,
        volume=700000,
        amount=19600000,
        change=0.20,
        change_percent=0.72,
        bid1=27.99,
        bid1_volume=800,
        ask1=28.01,
        ask1_volume=800,
        timestamp=time.time()
    ),
    "300308": Quote(
        code="300308",
        name="中际旭创",
        price=120.00,
        pre_close=118.00,
        open=119.00,
        high=121.50,
        low=118.50,
        volume=500000,
        amount=60000000,
        change=2.00,
        change_percent=1.69,
        bid1=119.99,
        bid1_volume=400,
        ask1=120.01,
        ask1_volume=400,
        timestamp=time.time()
    ),
    "600030": Quote(
        code="600030",
        name="中信证券",
        price=20.50,
        pre_close=20.30,
        open=20.40,
        high=20.70,
        low=20.20,
        volume=1500000,
        amount=30750000,
        change=0.20,
        change_percent=0.99,
        bid1=20.49,
        bid1_volume=2000,
        ask1=20.51,
        ask1_volume=2000,
        timestamp=time.time()
    ),
    "000725": Quote(
        code="000725",
        name="京东方A",
        price=3.80,
        pre_close=3.75,
        open=3.77,
        high=3.82,
        low=3.74,
        volume=2000000,
        amount=7600000,
        change=0.05,
        change_percent=1.33,
        bid1=3.79,
        bid1_volume=3000,
        ask1=3.81,
        ask1_volume=3000,
        timestamp=time.time()
    ),
    "600276": Quote(
        code="600276",
        name="恒瑞医药",
        price=42.00,
        pre_close=41.50,
        open=41.70,
        high=42.30,
        low=41.40,
        volume=600000,
        amount=25200000,
        change=0.50,
        change_percent=1.20,
        bid1=41.99,
        bid1_volume=600,
        ask1=42.01,
        ask1_volume=600,
        timestamp=time.time()
    ),
    "000651": Quote(
        code="000651",
        name="格力电器",
        price=35.00,
        pre_close=34.80,
        open=34.90,
        high=35.30,
        low=34.70,
        volume=700000,
        amount=24500000,
        change=0.20,
        change_percent=0.57,
        bid1=34.99,
        bid1_volume=700,
        ask1=35.01,
        ask1_volume=700,
        timestamp=time.time()
    ),
    "601899": Quote(
        code="601899",
        name="紫金矿业",
        price=15.50,
        pre_close=15.30,
        open=15.40,
        high=15.70,
        low=15.20,
        volume=1800000,
        amount=27900000,
        change=0.20,
        change_percent=1.31,
        bid1=15.49,
        bid1_volume=2500,
        ask1=15.51,
        ask1_volume=2500,
        timestamp=time.time()
    ),
    "002415": Quote(
        code="002415",
        name="海康威视",
        price=30.00,
        pre_close=29.70,
        open=29.80,
        high=30.20,
        low=29.60,
        volume=800000,
        amount=24000000,
        change=0.30,
        change_percent=1.01,
        bid1=29.99,
        bid1_volume=900,
        ask1=30.01,
        ask1_volume=900,
        timestamp=time.time()
    ),
    "600887": Quote(
        code="600887",
        name="伊利股份",
        price=45.00,
        pre_close=44.70,
        open=44.80,
        high=45.30,
        low=44.60,
        volume=500000,
        amount=22500000,
        change=0.30,
        change_percent=0.67,
        bid1=44.99,
        bid1_volume=500,
        ask1=45.01,
        ask1_volume=500,
        timestamp=time.time()
    ),
    "000002": Quote(
        code="000002",
        name="万科A",
        price=11.00,
        pre_close=10.90,
        open=10.95,
        high=11.10,
        low=10.85,
        volume=1200000,
        amount=13200000,
        change=0.10,
        change_percent=0.92,
        bid1=10.99,
        bid1_volume=1500,
        ask1=11.01,
        ask1_volume=1500,
        timestamp=time.time()
    ),
    "601328": Quote(
        code="601328",
        name="交通银行",
        price=5.80,
        pre_close=5.75,
        open=5.77,
        high=5.82,
        low=5.74,
        volume=1500000,
        amount=8700000,
        change=0.05,
        change_percent=0.87,
        bid1=5.79,
        bid1_volume=2000,
        ask1=5.81,
        ask1_volume=2000,
        timestamp=time.time()
    ),
}

# Stock search database for mock
MOCK_STOCKS = [
    {"code": "600519", "name": "贵州茅台", "market": "sh"},
    {"code": "000001", "name": "平安银行", "market": "sz"},
    {"code": "300750", "name": "宁德时代", "market": "sz"},
    {"code": "000858", "name": "五粮液", "market": "sz"},
    {"code":"688981","name":"中芯国际","market":"sh"},
    {"code":"601318","name":"中国平安","market":"sh"},
    {"code":"000333","name":"美的集团","market":"sz"},
    {"code":"600036","name":"招商银行","market":"sh"},
    {"code":"002594","name":"比亚迪","market":"sz"},
    {"code":"600900","name":"长江电力","market":"sh"},
    {"code":"300308","name":"中际旭创","market":"sz"},
    {"code":"600030","name":"中信证券","market":"sh"},
    {"code":"000725","name":"京东方A","market":"sz"},
    {"code":"600276","name":"恒瑞医药","market":"sh"},
    {"code":"000651","name":"格力电器","market":"sz"},
    {"code":"601899","name":"紫金矿业","market":"sh"},
    {"code":"002415","name":"海康威视","market":"sz"},
    {"code":"600887","name":"伊利股份","market":"sh"},
    {"code":"000002","name":"万科A","market":"sz"},
    {"code":"601328","name":"交通银行","market":"sh"},
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
            import random
            quote = MOCK_QUOTES[code]
            # Add some randomness to make it look real
            import copy
            quote = copy.deepcopy(quote)
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
