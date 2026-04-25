from __future__ import annotations

import asyncio

import yfinance as yf


async def fetch_price(symbol: str) -> tuple:
    """
    Returns (current_price, previous_close) for a symbol.
    Uses yfinance fast_info which supports pre-market prices during pre-market hours.
    """
    def _fetch() -> tuple:
        ticker = yf.Ticker(symbol)
        fast = ticker.fast_info
        price = fast.last_price
        prev_close = fast.previous_close
        if price is None or prev_close is None:
            raise ValueError(f"No price data available for {symbol}")
        return float(price), float(prev_close)

    return await asyncio.to_thread(_fetch)
