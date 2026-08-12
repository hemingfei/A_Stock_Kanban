"""Data sources for stock quotes."""

from typing import Optional
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
