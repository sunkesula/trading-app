from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Ticker, UserSubscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class SubscriptionCreate(BaseModel):
    user_id: uuid.UUID
    symbol: str


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    symbol: str
    active: bool

    model_config = {"from_attributes": True}


@router.get("/{user_id}", response_model=list)
async def list_subscriptions(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.active == True,
        )
    )
    return result.scalars().all()


@router.post("/", response_model=SubscriptionResponse, status_code=201)
async def subscribe(body: SubscriptionCreate, db: AsyncSession = Depends(get_db)):
    ticker = await db.get(Ticker, body.symbol.upper())
    if not ticker or not ticker.active:
        raise HTTPException(status_code=404, detail="Ticker not found or inactive")

    existing = await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == body.user_id,
            UserSubscription.symbol == body.symbol.upper(),
        )
    )
    sub = existing.scalar_one_or_none()
    if sub:
        sub.active = True
        await db.commit()
        await db.refresh(sub)
        return sub

    sub = UserSubscription(user_id=body.user_id, symbol=body.symbol.upper())
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete("/{user_id}/{symbol}", status_code=204)
async def unsubscribe(user_id: uuid.UUID, symbol: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.symbol == symbol.upper(),
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.active = False
    await db.commit()
