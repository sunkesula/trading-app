-- Stub users table (replaced by auth subsystem)
CREATE TABLE IF NOT EXISTS users (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tickers (
    symbol   VARCHAR(10) PRIMARY KEY,
    name     TEXT,
    active   BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_subscriptions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol        VARCHAR(10) NOT NULL REFERENCES tickers(symbol),
    active        BOOLEAN DEFAULT TRUE,
    subscribed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, symbol)
);

CREATE TABLE IF NOT EXISTS indicator_readings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol      VARCHAR(10) NOT NULL,
    indicator   VARCHAR(20) NOT NULL,
    timeframe   VARCHAR(5) NOT NULL,
    raw_value   JSONB NOT NULL,
    price       NUMERIC(10,4) NOT NULL,
    decision    VARCHAR(8) NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_indicator_readings_lookup
    ON indicator_readings (symbol, indicator, timeframe, recorded_at DESC);

CREATE TABLE IF NOT EXISTS indicator_thresholds (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    indicator         VARCHAR(20) NOT NULL,
    timeframe         VARCHAR(5) NOT NULL,
    bullish_threshold NUMERIC(10,4),
    bearish_threshold NUMERIC(10,4),
    notes             TEXT,
    UNIQUE(indicator, timeframe)
);

CREATE TABLE IF NOT EXISTS market_sentiment (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date         DATE NOT NULL,
    spy_price    NUMERIC(10,4) NOT NULL,
    qqq_price    NUMERIC(10,4) NOT NULL,
    spy_decision VARCHAR(8) NOT NULL,
    qqq_decision VARCHAR(8) NOT NULL,
    overall      VARCHAR(8) NOT NULL,
    recorded_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_market_sentiment_date_recorded
    ON market_sentiment (date, recorded_at DESC);

-- Seed system tickers
INSERT INTO tickers (symbol, name, active) VALUES
    ('SPY', 'SPDR S&P 500 ETF', TRUE),
    ('QQQ', 'Invesco QQQ Trust', TRUE)
ON CONFLICT (symbol) DO NOTHING;

-- Seed RSI thresholds
INSERT INTO indicator_thresholds (indicator, timeframe, bullish_threshold, bearish_threshold, notes) VALUES
    ('RSI', '1m',  25, 75, 'Tighter thresholds for 1-minute noise'),
    ('RSI', '5m',  30, 70, NULL),
    ('RSI', '15m', 30, 70, NULL)
ON CONFLICT (indicator, timeframe) DO NOTHING;
