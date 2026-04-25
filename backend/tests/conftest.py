import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/trading_app")
os.environ.setdefault("TAAPI_SECRET", "test_secret")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

import pytest
