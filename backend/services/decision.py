from __future__ import annotations

from typing import Literal

Decision = Literal["bullish", "bearish", "unsure"]


def compute_rsi_decision(
    value: float, bullish_threshold: float, bearish_threshold: float
) -> Decision:
    if value <= bullish_threshold:
        return "bullish"
    if value >= bearish_threshold:
        return "bearish"
    return "unsure"


def compute_bb_decision(price: float, upper_band: float, lower_band: float) -> Decision:
    if price <= lower_band * 1.02:
        return "bullish"
    if price >= upper_band * 0.98:
        return "bearish"
    return "unsure"


def compute_vwap_decision(price: float, vwap: float) -> Decision:
    if price > vwap * 1.001:
        return "bullish"
    if price < vwap * 0.999:
        return "bearish"
    return "unsure"


def compute_ma_decision(price: float, ma_value: float) -> Decision:
    if price > ma_value:
        return "bullish"
    return "bearish"


def compute_sentiment_decision(current_price: float, previous_close: float) -> Decision:
    if current_price > previous_close * 1.001:
        return "bullish"
    if current_price < previous_close * 0.999:
        return "bearish"
    return "unsure"


def compute_overall_sentiment(spy_decision: Decision, qqq_decision: Decision) -> Decision:
    if spy_decision == "bullish" and qqq_decision == "bullish":
        return "bullish"
    if spy_decision == "bearish" and qqq_decision == "bearish":
        return "bearish"
    return "unsure"
