import pytest
from unittest.mock import AsyncMock, patch, MagicMock


BULK_RESPONSE = {
    "data": [
        {"id": "rsi", "result": {"value": 45.67}},
        {"id": "bbands", "result": {
            "valueLowerBand": 148.5,
            "valueMiddleBand": 150.0,
            "valueUpperBand": 151.5,
        }},
        {"id": "vwap", "result": {"value": 150.3}},
    ]
}

MA_BULK_RESPONSE = {
    "data": [
        {"id": "ma_200", "result": {"value": 178.5}},
        {"id": "ma_150", "result": {"value": 180.2}},
        {"id": "ma_100", "result": {"value": 182.1}},
    ]
}


async def test_fetch_intraday_indicators_returns_parsed_results():
    with patch("backend.services.taapi.httpx.AsyncClient") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=BULK_RESPONSE)
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        from backend.services.taapi import fetch_intraday_indicators
        result = await fetch_intraday_indicators("AAPL", "1m")

    assert result["rsi"]["value"] == 45.67
    assert result["bbands"]["valueLowerBand"] == 148.5
    assert result["vwap"]["value"] == 150.3


async def test_fetch_ma_indicators_returns_parsed_results():
    with patch("backend.services.taapi.httpx.AsyncClient") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=MA_BULK_RESPONSE)
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        from backend.services.taapi import fetch_ma_indicators
        result = await fetch_ma_indicators("AAPL")

    assert result["ma_200"]["value"] == 178.5
    assert result["ma_150"]["value"] == 180.2
    assert result["ma_100"]["value"] == 182.1
