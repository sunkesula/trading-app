from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Ticker

router = APIRouter(prefix="/tickers", tags=["tickers"])


class TickerCreate(BaseModel):
    symbol: str
    name: Optional[str] = None


class TickerResponse(BaseModel):
    symbol: str
    name: Optional[str]
    active: bool

    model_config = {"from_attributes": True}


@router.get("/", response_model=list)
async def list_tickers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticker).where(Ticker.active == True))
    return result.scalars().all()


@router.post("/", response_model=TickerResponse, status_code=201)
async def add_ticker(body: TickerCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.get(Ticker, body.symbol.upper())
    if existing:
        raise HTTPException(status_code=409, detail="Ticker already exists")
    ticker = Ticker(symbol=body.symbol.upper(), name=body.name)
    db.add(ticker)
    await db.commit()
    await db.refresh(ticker)
    return ticker


@router.delete("/{symbol}", status_code=204)
async def deactivate_ticker(symbol: str, db: AsyncSession = Depends(get_db)):
    ticker = await db.get(Ticker, symbol.upper())
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    ticker.active = False
    await db.commit()
