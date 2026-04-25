from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Numeric,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    """Stub — replaced by the auth subsystem in a later plan."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Ticker(Base):
    __tablename__ = "tickers"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "symbol"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), ForeignKey("tickers.symbol"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndicatorReading(Base):
    __tablename__ = "indicator_readings"
    __table_args__ = (
        Index("ix_indicator_readings_lookup", "symbol", "indicator", "timeframe", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    indicator: Mapped[str] = mapped_column(String(20), nullable=False)  # RSI, BB, VWAP, MA_200, MA_150, MA_100
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False)   # 1m, 5m, 15m, 1d
    raw_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    decision: Mapped[str] = mapped_column(String(8), nullable=False)    # bullish, bearish, unsure
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndicatorThreshold(Base):
    __tablename__ = "indicator_thresholds"
    __table_args__ = (UniqueConstraint("indicator", "timeframe"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False)
    bullish_threshold: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    bearish_threshold: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class MarketSentiment(Base):
    __tablename__ = "market_sentiment"
    __table_args__ = (
        Index("ix_market_sentiment_date_recorded", "date", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    spy_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    qqq_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    spy_decision: Mapped[str] = mapped_column(String(8), nullable=False)
    qqq_decision: Mapped[str] = mapped_column(String(8), nullable=False)
    overall: Mapped[str] = mapped_column(String(8), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
