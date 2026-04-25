import pytest
from unittest.mock import AsyncMock, MagicMock, patch


async def test_poll_intraday_job_skips_outside_market_hours():
    with patch("backend.scheduler.jobs.is_market_hours", return_value=False):
        from backend.scheduler.jobs import poll_intraday_job
        with patch("backend.scheduler.jobs.fetch_intraday_indicators") as mock_taapi:
            await poll_intraday_job("1m")
            mock_taapi.assert_not_called()


async def test_poll_intraday_job_writes_readings_during_market_hours():
    mock_taapi_result = {
        "rsi": {"value": 45.0},
        "bbands": {"valueLowerBand": 148.0, "valueMiddleBand": 150.0, "valueUpperBand": 152.0},
        "vwap": {"value": 150.5},
    }
    mock_ticker = MagicMock()
    mock_ticker.symbol = "AAPL"

    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock(return_value=["AAPL"])
    mock_execute_result = MagicMock()
    mock_execute_result.scalars = MagicMock(return_value=mock_scalars)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_execute_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.scheduler.jobs.is_market_hours", return_value=True),
        patch("backend.scheduler.jobs.fetch_intraday_indicators", AsyncMock(return_value=mock_taapi_result)),
        patch("backend.scheduler.jobs.fetch_price", AsyncMock(return_value=(150.0, 148.5))),
        patch("backend.scheduler.jobs.set_price", AsyncMock()),
        patch("backend.scheduler.jobs.set_indicator", AsyncMock()),
        patch("backend.scheduler.jobs.manager") as mock_manager,
        patch("backend.scheduler.jobs.AsyncSessionLocal", return_value=mock_ctx),
        patch("backend.scheduler.jobs._load_rsi_thresholds", AsyncMock(return_value={("RSI", "1m"): (25.0, 75.0)})),
    ):
        mock_manager.broadcast_symbol = AsyncMock()
        from backend.scheduler.jobs import poll_intraday_job
        await poll_intraday_job("1m")

    mock_db.add.assert_called()
    mock_db.commit.assert_awaited()


async def test_update_market_sentiment_job_skips_before_premarket():
    with patch("backend.scheduler.jobs.is_premarket_or_market_hours", return_value=False):
        from backend.scheduler.jobs import update_market_sentiment_job
        with patch("backend.scheduler.jobs.fetch_price") as mock_price:
            await update_market_sentiment_job()
            mock_price.assert_not_called()
