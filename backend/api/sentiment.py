from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import MarketSentiment
from backend.services.cache import get_market_sentiment

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


class SentimentResponse(BaseModel):
    date: date
    spy_price: float
    qqq_price: float
    spy_decision: str
    qqq_decision: str
    overall: str

    model_config = {"from_attributes": True}


@router.get("/latest")
async def get_latest_sentiment(db: AsyncSession = Depends(get_db)):
    cached = await get_market_sentiment()
    if cached:
        return cached

    result = await db.execute(
        select(MarketSentiment).order_by(desc(MarketSentiment.recorded_at)).limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/today", response_model=list)
async def get_today_sentiment(db: AsyncSession = Depends(get_db)):
    today = date.today()
    result = await db.execute(
        select(MarketSentiment)
        .where(MarketSentiment.date == today)
        .order_by(desc(MarketSentiment.recorded_at))
    )
    return result.scalars().all()
