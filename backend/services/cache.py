from __future__ import annotations

import json
from typing import Optional

import redis.asyncio as aioredis

from backend.config import settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def set_price(symbol: str, price: float, ttl: int = 10) -> None:
    r = await get_redis()
    await r.setex(f"price:{symbol}", ttl, str(price))


async def get_price(symbol: str) -> Optional[float]:
    r = await get_redis()
    value = await r.get(f"price:{symbol}")
    return float(value) if value is not None else None


async def set_indicator(
    symbol: str,
    indicator: str,
    timeframe: str,
    data: dict,
    ttl: int,
) -> None:
    r = await get_redis()
    key = f"indicator:{symbol}:{indicator}:{timeframe}"
    await r.setex(key, ttl, json.dumps(data))


async def get_indicator(symbol: str, indicator: str, timeframe: str) -> Optional[dict]:
    r = await get_redis()
    key = f"indicator:{symbol}:{indicator}:{timeframe}"
    value = await r.get(key)
    return json.loads(value) if value is not None else None


async def set_market_sentiment(data: dict, ttl: int = 900) -> None:
    r = await get_redis()
    await r.setex("market_sentiment:latest", ttl, json.dumps(data))


async def get_market_sentiment() -> Optional[dict]:
    r = await get_redis()
    value = await r.get("market_sentiment:latest")
    return json.loads(value) if value is not None else None
