from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.scheduler.jobs import poll_intraday_job, poll_ma_job, update_market_sentiment_job

ET_TIMEZONE = "America/New_York"


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ET_TIMEZONE)

    # Market sentiment: every 15 min, Mon-Fri, 4:00 AM - 16:00 ET
    scheduler.add_job(
        update_market_sentiment_job,
        CronTrigger(day_of_week="mon-fri", hour="4-15", minute="*/15", timezone=ET_TIMEZONE),
        id="market_sentiment",
        name="Market Sentiment (SPY + QQQ)",
        max_instances=1,
        coalesce=True,
    )

    # Intraday 1m: every minute, Mon-Fri, 9:00-16:00 ET (job guards 9:30 cutoff internally)
    scheduler.add_job(
        lambda: poll_intraday_job("1m"),
        CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*", timezone=ET_TIMEZONE),
        id="poll_1m",
        name="Intraday poll 1m",
        max_instances=1,
        coalesce=True,
    )

    # Intraday 5m: every 5 minutes, Mon-Fri, 9:00-16:00 ET
    scheduler.add_job(
        lambda: poll_intraday_job("5m"),
        CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/5", timezone=ET_TIMEZONE),
        id="poll_5m",
        name="Intraday poll 5m",
        max_instances=1,
        coalesce=True,
    )

    # Intraday 15m: every 15 minutes, Mon-Fri, 9:00-16:00 ET
    scheduler.add_job(
        lambda: poll_intraday_job("15m"),
        CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/15", timezone=ET_TIMEZONE),
        id="poll_15m",
        name="Intraday poll 15m",
        max_instances=1,
        coalesce=True,
    )

    # MA daily: once at 9:30 AM ET, Mon-Fri
    scheduler.add_job(
        poll_ma_job,
        CronTrigger(day_of_week="mon-fri", hour=9, minute=30, timezone=ET_TIMEZONE),
        id="poll_ma_daily",
        name="MA 200/150/100 daily",
        max_instances=1,
        coalesce=True,
    )

    return scheduler
