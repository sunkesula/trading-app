from __future__ import annotations

import httpx

from backend.config import settings

TAAPI_URL = "https://api.taapi.io/bulk"

INTRADAY_INDICATORS = [
    {"id": "rsi", "indicator": "rsi"},
    {"id": "bbands", "indicator": "bbands"},
    {"id": "vwap", "indicator": "vwap"},
]

MA_INDICATORS = [
    {"id": "ma_200", "indicator": "sma", "period": 200},
    {"id": "ma_150", "indicator": "sma", "period": 150},
    {"id": "ma_100", "indicator": "sma", "period": 100},
]


def _parse_bulk_response(data: dict) -> dict:
    """Convert taapi.io data array into {id: result} mapping."""
    return {item["id"]: item["result"] for item in data["data"]}


async def fetch_intraday_indicators(symbol: str, timeframe: str) -> dict:
    """
    Calls taapi.io bulk endpoint for RSI, BB, VWAP for the given symbol and timeframe.
    Returns: {"rsi": {...}, "bbands": {...}, "vwap": {...}}
    """
    payload = {
        "secret": settings.taapi_secret,
        "construct": {
            "exchange": "stocks",
            "symbol": symbol,
            "interval": timeframe,
            "indicators": INTRADAY_INDICATORS,
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(TAAPI_URL, json=payload)
        response.raise_for_status()
        return _parse_bulk_response(response.json())


async def fetch_ma_indicators(symbol: str) -> dict:
    """
    Calls taapi.io bulk endpoint for MA_200, MA_150, MA_100 on the daily timeframe.
    Returns: {"ma_200": {...}, "ma_150": {...}, "ma_100": {...}}
    """
    payload = {
        "secret": settings.taapi_secret,
        "construct": {
            "exchange": "stocks",
            "symbol": symbol,
            "interval": "1d",
            "indicators": MA_INDICATORS,
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(TAAPI_URL, json=payload)
        response.raise_for_status()
        return _parse_bulk_response(response.json())
