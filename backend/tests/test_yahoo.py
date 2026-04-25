import pytest
from unittest.mock import MagicMock, patch


async def test_fetch_price_returns_current_price():
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 500.25
    mock_fast_info.previous_close = 498.00

    with patch("backend.services.yahoo.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.return_value.fast_info = mock_fast_info
        from backend.services.yahoo import fetch_price
        price, prev_close = await fetch_price("SPY")

    assert price == 500.25
    assert prev_close == 498.00


async def test_fetch_price_raises_on_missing_data():
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = None
    mock_fast_info.previous_close = None

    with patch("backend.services.yahoo.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.return_value.fast_info = mock_fast_info
        from backend.services.yahoo import fetch_price
        with pytest.raises(ValueError, match="No price data"):
            await fetch_price("INVALID")
