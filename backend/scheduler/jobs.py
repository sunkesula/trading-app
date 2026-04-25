from __future__ import annotations

import asyncio
import logging
from datetime import datetime, date
from typing import Optional

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models import IndicatorReading, IndicatorThreshold, MarketSentiment, Ticker
from backend.services.cache import set_indicator, set_market_sentiment, set_price
from backend.services.decision import (
    compute_bb_decision,
    compute_ma_decision,
    compute_overall_sentiment,
    compute_rsi_decision,
    compute_sentiment_decision,
    compute_vwap_decision,
)
from backend.services.taapi import fetch_intraday_indicators, fetch_ma_indicators
from backend.services.ws_manager import manager
from backend.services.yahoo import fetch_price

logger = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")

TIMEFRAME_TTL = {"1m": 60, "5m": 300, "15m": 900, "1d": 86400}


def is_market_hours() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    open_ = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_ <= now < close


def is_premarket_or_market_hours() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=4, minute=0, second=0, microsecond=0)
    close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return start <= now < close


async def _load_rsi_thresholds(session: AsyncSession) -> dict:
    result = await session.execute(
        select(IndicatorThreshold).where(IndicatorThreshold.indicator == "RSI")
    )
    thresholds = result.scalars().all()
    return {
        (t.indicator, t.timeframe): (float(t.bullish_threshold), float(t.bearish_threshold))
        for t in thresholds
    }


async def _get_active_tickers(session: AsyncSession) -> list:
    result = await session.execute(select(Ticker.symbol).where(Ticker.active == True))
    return list(result.scalars().all())


async def poll_intraday_job(timeframe: str) -> None:
    """Poll RSI, BB, VWAP for all active tickers at the given timeframe."""
    if not is_market_hours():
        return

    async with AsyncSessionLocal() as session:
        symbols = await _get_active_tickers(session)
        rsi_thresholds = await _load_rsi_thresholds(session)

        for symbol in symbols:
            try:
                taapi_data, prices = await asyncio.gather(
                    fetch_intraday_indicators(symbol, timeframe),
                    fetch_price(symbol),
                )
                price, _ = prices
                await set_price(symbol, price)

                readings = _build_intraday_readings(symbol, timeframe, taapi_data, price, rsi_thresholds)

                for reading in readings:
                    session.add(reading)
                    await set_indicator(
                        symbol, reading.indicator, timeframe,
                        {"raw_value": reading.raw_value, "decision": reading.decision, "price": price},
                        ttl=TIMEFRAME_TTL[timeframe],
                    )
                    await manager.broadcast_symbol(symbol, {
                        "event": "indicator_update",
                        "symbol": symbol,
                        "indicator": reading.indicator,
                        "timeframe": timeframe,
                        "raw_value": reading.raw_value,
                        "decision": reading.decision,
                        "price": price,
                        "timestamp": datetime.now(ET).isoformat(),
                    })

                await session.commit()
            except Exception as e:
                logger.error("Error polling %s at %s: %s", symbol, timeframe, e)


def _build_intraday_readings(
    symbol: str,
    timeframe: str,
    taapi_data: dict,
    price: float,
    rsi_thresholds: dict,
) -> list:
    readings = []

    if "rsi" in taapi_data:
        raw = taapi_data["rsi"]
        bullish_t, bearish_t = rsi_thresholds.get(("RSI", timeframe), (30.0, 70.0))
        decision = compute_rsi_decision(raw["value"], bullish_t, bearish_t)
        readings.append(IndicatorReading(
            symbol=symbol, indicator="RSI", timeframe=timeframe,
            raw_value=raw, price=price, decision=decision,
        ))

    if "bbands" in taapi_data:
        raw = taapi_data["bbands"]
        decision = compute_bb_decision(price, raw["valueUpperBand"], raw["valueLowerBand"])
        readings.append(IndicatorReading(
            symbol=symbol, indicator="BB", timeframe=timeframe,
            raw_value=raw, price=price, decision=decision,
        ))

    if "vwap" in taapi_data:
        raw = taapi_data["vwap"]
        decision = compute_vwap_decision(price, raw["value"])
        readings.append(IndicatorReading(
            symbol=symbol, indicator="VWAP", timeframe=timeframe,
            raw_value=raw, price=price, decision=decision,
        ))

    return readings


async def poll_ma_job() -> None:
    """Poll MA_200, MA_150, MA_100 for all active tickers. Runs once at 9:30 AM ET."""
    async with AsyncSessionLocal() as session:
        symbols = await _get_active_tickers(session)

        for symbol in symbols:
            try:
                ma_data = await fetch_ma_indicators(symbol)
                price, _ = await fetch_price(symbol)

                for ma_id, indicator_name in [("ma_200", "MA_200"), ("ma_150", "MA_150"), ("ma_100", "MA_100")]:
                    if ma_id not in ma_data:
                        continue
                    raw = ma_data[ma_id]
                    decision = compute_ma_decision(price, raw["value"])
                    reading = IndicatorReading(
                        symbol=symbol, indicator=indicator_name, timeframe="1d",
                        raw_value=raw, price=price, decision=decision,
                    )
                    session.add(reading)
                    await set_indicator(
                        symbol, indicator_name, "1d",
                        {"raw_value": raw, "decision": decision, "price": price},
                        ttl=TIMEFRAME_TTL["1d"],
                    )
                    await manager.broadcast_symbol(symbol, {
                        "event": "indicator_update",
                        "symbol": symbol,
                        "indicator": indicator_name,
                        "timeframe": "1d",
                        "raw_value": raw,
                        "decision": decision,
                        "price": price,
                        "timestamp": datetime.now(ET).isoformat(),
                    })

                await session.commit()
            except Exception as e:
                logger.error("Error polling MA for %s: %s", symbol, e)


async def update_market_sentiment_job() -> None:
    """Fetch SPY + QQQ prices and write a market_sentiment row. Runs every 15 min from 4 AM ET."""
    if not is_premarket_or_market_hours():
        return

    try:
        spy_price, spy_prev_close = await fetch_price("SPY")
        qqq_price, qqq_prev_close = await fetch_price("QQQ")

        spy_decision = compute_sentiment_decision(spy_price, spy_prev_close)
        qqq_decision = compute_sentiment_decision(qqq_price, qqq_prev_close)
        overall = compute_overall_sentiment(spy_decision, qqq_decision)

        today = date.today()
        sentiment = MarketSentiment(
            date=today,
            spy_price=spy_price,
            qqq_price=qqq_price,
            spy_decision=spy_decision,
            qqq_decision=qqq_decision,
            overall=overall,
        )

        async with AsyncSessionLocal() as session:
            session.add(sentiment)
            await session.commit()

        payload = {
            "event": "market_sentiment",
            "date": today.isoformat(),
            "spy_price": spy_price,
            "qqq_price": qqq_price,
            "spy_decision": spy_decision,
            "qqq_decision": qqq_decision,
            "overall": overall,
            "timestamp": datetime.now(ET).isoformat(),
        }
        await set_market_sentiment(payload)
        await manager.broadcast_all(payload)

    except Exception as e:
        logger.error("Error updating market sentiment: %s", e)
