CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS strategy;
CREATE SCHEMA IF NOT EXISTS risk;
CREATE SCHEMA IF NOT EXISTS backtesting;
CREATE SCHEMA IF NOT EXISTS execution;

CREATE TABLE IF NOT EXISTS candles (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(28, 12) NOT NULL,
    high NUMERIC(28, 12) NOT NULL,
    low NUMERIC(28, 12) NOT NULL,
    close NUMERIC(28, 12) NOT NULL,
    volume NUMERIC(28, 12) NOT NULL,
    CONSTRAINT uq_candles_symbol_timeframe_timestamp UNIQUE (symbol, timeframe, timestamp)
);

CREATE INDEX IF NOT EXISTS ix_candles_symbol ON candles (symbol);
CREATE INDEX IF NOT EXISTS ix_candles_timeframe ON candles (timeframe);
CREATE INDEX IF NOT EXISTS ix_candles_timestamp ON candles (timestamp);

CREATE TABLE IF NOT EXISTS paper_trades (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    side VARCHAR(8) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'OPEN',
    confidence NUMERIC(10, 6) NOT NULL,
    leverage NUMERIC(10, 4) NOT NULL,
    quantity NUMERIC(28, 12) NOT NULL,
    entry_price NUMERIC(28, 12) NOT NULL,
    exit_price NUMERIC(28, 12),
    stop_loss NUMERIC(28, 12),
    take_profit NUMERIC(28, 12),
    notional NUMERIC(28, 12) NOT NULL,
    pnl NUMERIC(28, 12),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_paper_trades_symbol ON paper_trades (symbol);
CREATE INDEX IF NOT EXISTS ix_paper_trades_status ON paper_trades (status);
