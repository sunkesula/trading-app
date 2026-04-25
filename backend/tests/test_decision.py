import pytest
from backend.services.decision import (
    compute_rsi_decision,
    compute_bb_decision,
    compute_vwap_decision,
    compute_ma_decision,
    compute_sentiment_decision,
    compute_overall_sentiment,
)

# RSI
def test_rsi_bullish():
    assert compute_rsi_decision(24.0, bullish_threshold=25.0, bearish_threshold=75.0) == "bullish"

def test_rsi_bullish_at_threshold():
    assert compute_rsi_decision(25.0, bullish_threshold=25.0, bearish_threshold=75.0) == "bullish"

def test_rsi_bearish():
    assert compute_rsi_decision(76.0, bullish_threshold=25.0, bearish_threshold=75.0) == "bearish"

def test_rsi_bearish_at_threshold():
    assert compute_rsi_decision(75.0, bullish_threshold=25.0, bearish_threshold=75.0) == "bearish"

def test_rsi_unsure():
    assert compute_rsi_decision(50.0, bullish_threshold=25.0, bearish_threshold=75.0) == "unsure"

# Bollinger Bands
def test_bb_bullish():
    # price=149.0 <= lower_band(148.0) * 1.02 = 150.96 -> bullish
    assert compute_bb_decision(price=149.0, upper_band=160.0, lower_band=148.0) == "bullish"

def test_bb_bearish():
    # price=157.0 >= upper_band(160.0) * 0.98 = 156.8 -> bearish
    assert compute_bb_decision(price=157.0, upper_band=160.0, lower_band=148.0) == "bearish"

def test_bb_unsure():
    # price=154.0 is between 150.96 and 156.8
    assert compute_bb_decision(price=154.0, upper_band=160.0, lower_band=148.0) == "unsure"

# VWAP
def test_vwap_bullish():
    # price=151.0 > vwap(150.0) * 1.001 = 150.15 -> bullish
    assert compute_vwap_decision(price=151.0, vwap=150.0) == "bullish"

def test_vwap_bearish():
    # price=149.0 < vwap(150.0) * 0.999 = 149.85 -> bearish
    assert compute_vwap_decision(price=149.0, vwap=150.0) == "bearish"

def test_vwap_unsure():
    # price=150.05 is within 0.1% of 150.0
    assert compute_vwap_decision(price=150.05, vwap=150.0) == "unsure"

# Moving Average
def test_ma_bullish():
    assert compute_ma_decision(price=180.0, ma_value=175.0) == "bullish"

def test_ma_bearish():
    assert compute_ma_decision(price=170.0, ma_value=175.0) == "bearish"

# Market Sentiment
def test_sentiment_bullish():
    # price 0.2% above prev close -> bullish
    assert compute_sentiment_decision(current_price=500.5, previous_close=500.0) == "bullish"

def test_sentiment_bearish():
    # price 0.12% below prev close -> bearish
    assert compute_sentiment_decision(current_price=499.4, previous_close=500.0) == "bearish"

def test_sentiment_unsure():
    # price within 0.1% of prev close
    assert compute_sentiment_decision(current_price=500.05, previous_close=500.0) == "unsure"

def test_overall_both_bullish():
    assert compute_overall_sentiment("bullish", "bullish") == "bullish"

def test_overall_both_bearish():
    assert compute_overall_sentiment("bearish", "bearish") == "bearish"

def test_overall_mixed():
    assert compute_overall_sentiment("bullish", "bearish") == "unsure"

def test_overall_unsure_and_bullish():
    assert compute_overall_sentiment("unsure", "bullish") == "unsure"
