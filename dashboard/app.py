from __future__ import annotations

import json
import os
from html import escape
from datetime import UTC, date, datetime, time, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


REQUEST_TIMEOUT_SECONDS = 240
INITIAL_CAPITAL = 10_000.0
TAKER_FEE_RATE = 0.0005
TIMEFRAME_TO_MINUTES = {
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
}

MARKET_DATA_SERVICE_URL = os.getenv("MARKET_DATA_SERVICE_URL", "http://127.0.0.1:8001")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8002")
STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", "http://127.0.0.1:8003")
RISK_MANAGER_URL = os.getenv("RISK_MANAGER_URL", "http://127.0.0.1:8004")
BACKTESTING_SERVICE_URL = os.getenv("BACKTESTING_SERVICE_URL", "http://127.0.0.1:8005")

DEFAULT_HISTORY_END_DATE = date(2026, 5, 23)
DEFAULT_TODAY = datetime.now(tz=UTC).date()
DEFAULT_LONG_HISTORY_END_DATE = min(DEFAULT_HISTORY_END_DATE, DEFAULT_TODAY)

COLOR_BG = "#0b0f14"
COLOR_SURFACE = "#111820"
COLOR_SURFACE_ALT = "#151d26"
COLOR_BORDER = "#263241"
COLOR_TEXT = "#e6edf3"
COLOR_MUTED = "#8a96a8"
COLOR_GREEN = "#00c087"
COLOR_RED = "#f6465d"
COLOR_YELLOW = "#f0b90b"
COLOR_BLUE = "#3b82f6"

PERCENT_COLUMNS = {
    "Доходность",
    "Доходность %",
    "Return",
    "Return %",
    "Winrate",
    "Просадка",
    "Max Drawdown",
    "Target=1",
}
PROBABILITY_COLUMNS = {
    "Вероятность",
    "Probability",
    "Средняя вероятность",
    "Макс. вероятность",
    "Entry",
    "Порог входа",
}
MONEY_COLUMNS = {
    "PnL",
    "Сумма PnL",
    "Худшее окно",
    "Грубый PnL",
    "Комиссии",
    "Чистый PnL",
    "Net PnL",
    "Капитал",
}
PRICE_COLUMNS = {
    "Цена",
    "Цена входа",
    "Цена выхода",
    "Entry price",
    "Exit price",
    "Stop-loss",
    "Take-profit",
}
DATE_COLUMNS = {
    "Время",
    "Вход",
    "Выход",
    "Начало",
    "Конец",
    "Train start",
    "Train end",
    "Test start",
    "Test end",
}


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {COLOR_BG};
            --surface: {COLOR_SURFACE};
            --surface-alt: {COLOR_SURFACE_ALT};
            --border: {COLOR_BORDER};
            --text: {COLOR_TEXT};
            --muted: {COLOR_MUTED};
            --green: {COLOR_GREEN};
            --red: {COLOR_RED};
            --yellow: {COLOR_YELLOW};
            --blue: {COLOR_BLUE};
        }}

        .stApp {{
            background: var(--bg);
            color: var(--text);
        }}

        header[data-testid="stHeader"] {{
            height: 0;
            min-height: 0;
            background: transparent;
        }}

        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        #MainMenu {{
            display: none;
            visibility: hidden;
            height: 0;
        }}

        section[data-testid="stSidebar"] {{
            background: #0d131a;
            border-right: 1px solid var(--border);
        }}

        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label,
        .stSlider label,
        .stSelectbox label,
        .stNumberInput label {{
            color: #c8d2df;
            font-size: 12px;
            letter-spacing: 0;
            font-weight: 600;
        }}

        .block-container {{
            max-width: 1600px;
            padding-top: 0.4rem;
            padding-bottom: 2rem;
        }}

        .trading-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 10px 0 14px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 12px;
        }}

        .brand-wrap {{
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }}

        .brand-mark {{
            width: 34px;
            height: 34px;
            border-radius: 6px;
            background: var(--green);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #07110d;
            font-weight: 900;
            font-size: 18px;
        }}

        .brand-title {{
            color: var(--text);
            font-size: 21px;
            font-weight: 700;
            line-height: 1.1;
            letter-spacing: 0;
        }}

        .brand-subtitle {{
            color: var(--muted);
            font-size: 12px;
            margin-top: 2px;
        }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }}

        .status-pill {{
            color: var(--green);
            background: rgba(0, 192, 135, 0.10);
            border: 1px solid rgba(0, 192, 135, 0.35);
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
            white-space: nowrap;
        }}

        .mode-pill {{
            color: var(--yellow);
            background: rgba(240, 185, 11, 0.10);
            border: 1px solid rgba(240, 185, 11, 0.35);
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
            white-space: nowrap;
        }}

        .market-strip {{
            display: grid;
            grid-template-columns: repeat(6, minmax(120px, 1fr));
            gap: 8px;
            margin: 4px 0 10px;
        }}

        .market-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px 12px;
            min-height: 70px;
        }}

        .market-label {{
            color: var(--muted);
            font-size: 11px;
            margin-bottom: 5px;
        }}

        .market-value {{
            color: var(--text);
            font-size: 20px;
            font-weight: 700;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }}

        .market-value.small {{
            font-size: 16px;
        }}

        .positive {{
            color: var(--green);
        }}

        .negative {{
            color: var(--red);
        }}

        .section-title {{
            color: var(--text);
            font-size: 15px;
            font-weight: 700;
            margin: 0 0 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }}

        h1, h2, h3 {{
            color: var(--text);
            letter-spacing: 0;
        }}

        h3 {{
            font-size: 15px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
            margin-top: 0;
        }}

        div[data-testid="stMetric"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px 12px;
            min-height: 86px;
        }}

        div[data-testid="stMetricLabel"] p {{
            color: var(--muted);
            font-size: 12px;
        }}

        div[data-testid="stMetricValue"] {{
            color: var(--text);
            font-size: 24px;
        }}

        .stButton > button {{
            background: var(--green);
            color: #06110d;
            border: 1px solid var(--green);
            border-radius: 4px;
            font-weight: 700;
            min-height: 38px;
            transition: background 120ms ease, border-color 120ms ease;
        }}

        .stButton > button:hover {{
            background: #23d39d;
            border-color: #23d39d;
            color: #06110d;
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {{
            background: #0f1720;
            border: 1px solid #3a4657;
            border-radius: 4px;
        }}

        div[data-baseweb="select"] {{
            color: var(--text) !important;
        }}

        div[data-baseweb="select"] > div {{
            min-height: 40px;
        }}

        div[data-baseweb="select"] div,
        div[data-baseweb="select"] input {{
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
            font-weight: 700;
        }}

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg,
        input,
        textarea,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextInput"] input {{
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
            caret-color: var(--green);
        }}

        div[data-baseweb="input"] input,
        div[data-testid="stNumberInput"] input {{
            background: #0f1720 !important;
            font-weight: 700;
        }}

        input::placeholder,
        textarea::placeholder {{
            color: #aab6c6 !important;
            -webkit-text-fill-color: #aab6c6 !important;
            opacity: 1;
        }}

        div[data-baseweb="input"]:focus-within > div,
        div[data-baseweb="select"]:focus-within > div {{
            border-color: var(--green);
            box-shadow: 0 0 0 1px rgba(0, 192, 135, 0.45);
        }}

        div[role="listbox"],
        ul[role="listbox"],
        div[data-baseweb="popover"] {{
            background: #0f1720 !important;
            border: 1px solid #3a4657 !important;
            color: var(--text) !important;
            box-shadow: 0 16px 30px rgba(0, 0, 0, 0.45) !important;
        }}

        div[data-baseweb="popover"] > div,
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] div {{
            background-color: #0f1720 !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }}

        div[role="option"],
        li[role="option"] {{
            background: #0f1720 !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
            font-weight: 700;
        }}

        div[role="option"]:hover,
        li[role="option"]:hover,
        div[aria-selected="true"],
        li[aria-selected="true"],
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="popover"] li:hover div,
        div[data-baseweb="popover"] li[aria-selected="true"],
        div[data-baseweb="popover"] li[aria-selected="true"] div {{
            background: #162332 !important;
            color: var(--green) !important;
            -webkit-text-fill-color: var(--green) !important;
        }}

        button[kind="secondary"],
        div[data-testid="stNumberInput"] button {{
            background: #f3f6fa;
            color: #0b0f14;
            border-color: #d7dee8;
        }}

        div[data-testid="stNumberInput"] button svg {{
            color: #0b0f14;
            fill: #0b0f14;
        }}

        div[data-testid="stSlider"] [data-testid="stTickBar"] {{
            color: #d5dde8;
        }}

        div[data-testid="stSlider"] div[role="slider"] {{
            background: var(--red);
            border-color: var(--red);
        }}

        div[data-testid="stAlert"] * {{
            color: #dce7f5;
        }}

        div[data-testid="stDataFrame"],
        div[data-testid="stPlotlyChart"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px;
            box-sizing: border-box;
            max-width: 100%;
            overflow: hidden;
        }}

        div[data-testid="stPlotlyChart"] > div {{
            max-width: 100%;
        }}

        .dark-table-wrap {{
            max-height: 430px;
            overflow: auto;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
        }}

        .dark-table {{
            width: 100%;
            border-collapse: collapse;
            color: var(--text);
            font-size: 13px;
            line-height: 1.35;
        }}

        .dark-table thead th {{
            position: sticky;
            top: 0;
            z-index: 1;
            background: #182231;
            color: #dce7f5;
            border-bottom: 1px solid #344154;
            padding: 9px 10px;
            text-align: left;
            font-weight: 700;
            white-space: nowrap;
        }}

        .dark-table tbody td {{
            background: #101821;
            border-bottom: 1px solid #223044;
            color: #e6edf3;
            padding: 8px 10px;
            vertical-align: top;
            white-space: nowrap;
        }}

        .dark-table tbody tr:nth-child(even) td {{
            background: #0d151e;
        }}

        .dark-table tbody tr:hover td {{
            background: #162332;
        }}

        .dark-table .num {{
            text-align: right;
            font-variant-numeric: tabular-nums;
        }}

        .dark-table-empty {{
            color: #c8d2df;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 14px;
            font-size: 13px;
        }}

        div[data-testid="stAlert"] {{
            background: var(--surface-alt);
            border: 1px solid var(--border);
            color: var(--text);
        }}

        .stExpander {{
            border-color: var(--border);
            background: var(--surface);
        }}

        button[data-baseweb="tab"] {{
            color: var(--muted);
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--green);
        }}

        @media (max-width: 900px) {{
            .market-strip {{
                grid-template-columns: repeat(2, minmax(120px, 1fr));
            }}
            .trading-header {{
                align-items: flex-start;
                flex-direction: column;
            }}
            .header-actions {{
                justify-content: flex-start;
            }}
        }}

        code {{
            color: var(--green);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.ok:
        return response.json()

    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    raise RuntimeError(f"{response.status_code} {response.reason}: {detail}")


def estimate_candle_count(*, timeframe: str, history_months: int) -> int:
    minutes = TIMEFRAME_TO_MINUTES.get(timeframe, 60)
    return int((history_months * 30 * 24 * 60) / minutes)


def estimate_candle_count_for_dates(*, timeframe: str, start_date: date, end_date: date) -> int:
    minutes = TIMEFRAME_TO_MINUTES.get(timeframe, 60)
    days = max(0, (end_date - start_date).days + 1)
    return int((days * 24 * 60) / minutes)


def get_walk_forward_grid_ranges(*, timeframe: str, trade_mode: str) -> tuple[list[float], list[float]]:
    if timeframe == "4h":
        if trade_mode == "short_only":
            return [0.006, 0.008, 0.010, 0.012], [0.50, 0.52, 0.54, 0.55, 0.58, 0.60]
        return [0.008, 0.010, 0.012, 0.014], [0.48, 0.50, 0.52, 0.54, 0.55, 0.56]
    if timeframe == "1h":
        return [0.005, 0.006, 0.008, 0.010], [0.50, 0.55, 0.60, 0.65]
    if timeframe in {"15m", "30m"}:
        return [0.003, 0.004, 0.005, 0.006], [0.45, 0.50, 0.55, 0.60]
    return [0.002, 0.003, 0.004, 0.005], [0.45, 0.50, 0.55, 0.60]


def estimate_walk_forward_required_rows(*, train_window: int, test_window: int, feature_set: str, horizon: int) -> int:
    warmup_rows = 260 if feature_set == "v2" else 80
    return train_window + test_window + warmup_rows + horizon


def estimate_walk_forward_max_folds(
    *,
    estimated_rows: int,
    train_window: int,
    test_window: int,
    feature_set: str,
    horizon: int,
) -> int:
    warmup_rows = 260 if feature_set == "v2" else 80
    usable_rows = max(0, estimated_rows - warmup_rows - horizon)
    if usable_rows < train_window + test_window:
        return 0
    return 1 + ((usable_rows - train_window - test_window) // test_window)


def estimate_walk_forward_coverage_days(*, timeframe: str, test_window: int, max_folds: int) -> float:
    minutes = TIMEFRAME_TO_MINUTES.get(timeframe, 60)
    return (test_window * max_folds * minutes) / (24 * 60)


def has_enough_rows_for_walk_forward(
    candles: pd.DataFrame,
    *,
    train_window: int,
    test_window: int,
    feature_set: str,
    horizon: int,
) -> tuple[bool, int, int]:
    required_rows = estimate_walk_forward_required_rows(
        train_window=train_window,
        test_window=test_window,
        feature_set=feature_set,
        horizon=horizon,
    )
    loaded_rows = len(candles)
    return loaded_rows >= required_rows, loaded_rows, required_rows


def fetch_market_data(
    symbol: str,
    timeframe: str,
    history_months: int,
    history_end_date: date,
    history_start_date: date | None = None,
) -> pd.DataFrame:
    rows_by_timestamp: dict[str, dict[str, object]] = {}
    requested_end_time = datetime.combine(history_end_date, time.max, tzinfo=UTC)
    now_utc = datetime.now(tz=UTC)
    end_time: pd.Timestamp | None = pd.Timestamp(min(requested_end_time, now_utc))
    if history_start_date is None:
        start_time = end_time - pd.DateOffset(months=history_months)
    else:
        start_time = pd.Timestamp(datetime.combine(history_start_date, time.min, tzinfo=UTC))

    if start_time >= end_time:
        raise ValueError("Дата начала истории должна быть раньше даты окончания.")

    while end_time is not None and end_time > start_time:
        payload: dict[str, object] = {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": 1440,
            "end_time": end_time.isoformat(),
        }

        response = post_json(f"{MARKET_DATA_SERVICE_URL}/fetch-candles", payload)
        candles = response.get("candles", [])
        if not candles:
            break

        chunk = pd.DataFrame(candles)
        chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], utc=True)
        for row in chunk.to_dict("records"):
            rows_by_timestamp[row["timestamp"].isoformat()] = row

        oldest_timestamp = chunk["timestamp"].min()
        if oldest_timestamp <= start_time:
            break

        next_end_time = oldest_timestamp - timedelta(milliseconds=1)
        if next_end_time >= end_time:
            break
        end_time = next_end_time

    candles = pd.DataFrame(rows_by_timestamp.values())
    if candles.empty:
        return candles

    numeric_columns = ["open", "high", "low", "close", "volume"]
    candles[numeric_columns] = candles[numeric_columns].astype(float)
    candles = candles[candles["timestamp"] >= start_time]
    return candles.sort_values("timestamp").reset_index(drop=True)


def train_model(
    candles: pd.DataFrame,
    *,
    symbol: str,
    horizon: int,
    threshold: float,
    feature_set: str,
    target_direction: str,
) -> dict[str, object]:
    endpoint = "/train-v2" if feature_set == "v2" else "/train"
    payload = {
        "candles": dataframe_to_candles(candles),
        "horizon": horizon,
        "threshold": threshold,
        "target_mode": "barrier",
        "target_direction": target_direction,
        "stop_loss_threshold": max(threshold / 2, TAKER_FEE_RATE * 4),
        "test_size": 0.2,
        "model_name": f"{symbol.lower().replace('-', '_')}_{feature_set}",
        "random_state": 42,
    }
    return post_json(f"{ML_SERVICE_URL}{endpoint}", payload)


def run_walk_forward(
    candles: pd.DataFrame,
    *,
    symbol: str,
    horizon: int,
    threshold: float,
    feature_set: str,
    target_direction: str,
    train_window: int,
    test_window: int,
    step_size: int,
    max_folds: int,
) -> dict[str, object]:
    endpoint = "/walk-forward-v2" if feature_set == "v2" else "/walk-forward"
    payload = {
        "candles": dataframe_to_candles(candles),
        "horizon": horizon,
        "threshold": threshold,
        "target_mode": "barrier",
        "target_direction": target_direction,
        "stop_loss_threshold": max(threshold / 2, TAKER_FEE_RATE * 4),
        "test_size": 0.2,
        "model_name": f"{symbol.lower().replace('-', '_')}_{feature_set}_walk_forward",
        "random_state": 42,
        "train_window": train_window,
        "test_window": test_window,
        "step_size": step_size,
        "max_folds": max_folds,
    }
    return post_json(f"{ML_SERVICE_URL}{endpoint}", payload)


def run_walk_forward_for_mode(
    candles: pd.DataFrame,
    *,
    symbol: str,
    horizon: int,
    threshold: float,
    feature_set: str,
    trade_mode: str,
    train_window: int,
    test_window: int,
    step_size: int,
    max_folds: int,
) -> dict[str, object]:
    if trade_mode == "short_only":
        return run_walk_forward(
            candles,
            symbol=symbol,
            horizon=horizon,
            threshold=threshold,
            feature_set=feature_set,
            target_direction="short",
            train_window=train_window,
            test_window=test_window,
            step_size=step_size,
            max_folds=max_folds,
        )
    return run_walk_forward(
        candles,
        symbol=symbol,
        horizon=horizon,
        threshold=threshold,
        feature_set=feature_set,
        target_direction="long",
        train_window=train_window,
        test_window=test_window,
        step_size=step_size,
        max_folds=max_folds,
    )


def build_mode_predictions(
    *,
    candles: pd.DataFrame,
    symbol: str,
    horizon: int,
    threshold: float,
    feature_set: str,
    trade_mode: str,
    train_window: int,
    test_window: int,
    step_size: int,
    max_folds: int,
) -> tuple[dict[str, object], pd.DataFrame]:
    long_walk_forward = run_walk_forward(
        candles,
        symbol=symbol,
        horizon=horizon,
        threshold=threshold,
        feature_set=feature_set,
        target_direction="long",
        train_window=train_window,
        test_window=test_window,
        step_size=step_size,
        max_folds=max_folds,
    )
    long_predictions = predictions_to_dataframe(long_walk_forward)

    if trade_mode == "long_only":
        long_predictions["signal_direction"] = "long"
        return long_walk_forward, long_predictions

    short_walk_forward = run_walk_forward(
        candles,
        symbol=symbol,
        horizon=horizon,
        threshold=threshold,
        feature_set=feature_set,
        target_direction="short",
        train_window=train_window,
        test_window=test_window,
        step_size=step_size,
        max_folds=max_folds,
    )
    short_predictions = predictions_to_dataframe(short_walk_forward)
    short_predictions["signal_direction"] = "short"

    if trade_mode == "short_only":
        return short_walk_forward, short_predictions

    combined = combine_long_short_predictions(long_predictions, short_predictions)
    return long_walk_forward, combined


def combine_long_short_predictions(long_predictions: pd.DataFrame, short_predictions: pd.DataFrame) -> pd.DataFrame:
    if long_predictions.empty:
        return short_predictions
    if short_predictions.empty:
        long_predictions = long_predictions.copy()
        long_predictions["signal_direction"] = "long"
        return long_predictions

    long_predictions = long_predictions.copy()
    short_predictions = short_predictions.copy()
    long_predictions["signal_direction"] = "long"
    short_predictions["signal_direction"] = "short"

    combined = pd.concat([long_predictions, short_predictions], ignore_index=True)
    combined["direction_priority"] = combined["signal_direction"].map({"long": 0, "short": 1}).fillna(2)
    combined = combined.sort_values(
        by=["timestamp", "direction_priority", "probability"],
        ascending=[True, True, False],
        kind="mergesort",
    ).drop(columns=["direction_priority"])
    return combined.reset_index(drop=True)


def run_walk_forward_grid(
    candles: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    horizon: int,
    feature_set: str,
    trade_mode: str,
    trend_filter_mode: str,
    stop_loss_mode: str,
    atr_multiplier: float,
    risk_reward_ratio: float,
    train_window: int,
    test_window: int,
    step_size: int,
    max_folds: int,
    cooldown_after_stop_loss: int = 0,
    cooldown_after_take_profit: int = 0,
    cooldown_after_time_exit: int = 0,
    rearm_probability_threshold: float | None = None,
) -> pd.DataFrame:
    target_values, entry_values = get_walk_forward_grid_ranges(timeframe=timeframe, trade_mode=trade_mode)
    rows: list[dict[str, object]] = []

    for target_value in target_values:
        walk_forward, predictions = build_mode_predictions(
            candles=candles,
            symbol=symbol,
            horizon=horizon,
            threshold=target_value,
            feature_set=feature_set,
            trade_mode=trade_mode,
            train_window=train_window,
            test_window=test_window,
            step_size=step_size,
            max_folds=max_folds,
        )
        signals = generate_signals(symbol=symbol, predictions=predictions, trend_filter_mode=trend_filter_mode)
        blocked_count = int((signals.get("reason") == "blocked_by_trend_filter").sum())

        for entry_value in entry_values:
            backtest = run_backtest(
                signals,
                probability_threshold=entry_value,
                target_threshold=target_value,
                stop_loss_mode=stop_loss_mode,
                atr_multiplier=atr_multiplier,
                risk_reward_ratio=risk_reward_ratio,
                horizon=horizon,
                cooldown_after_stop_loss=cooldown_after_stop_loss,
                cooldown_after_take_profit=cooldown_after_take_profit,
                cooldown_after_time_exit=cooldown_after_time_exit,
                rearm_probability_threshold=rearm_probability_threshold,
            )
            rows.append(
                {
                    "target": target_value,
                    "entry": entry_value,
                    "pnl": float(backtest["total_pnl"]),
                    "return_pct": float(backtest["total_return_pct"]),
                    "winrate": float(backtest["winrate"]),
                    "max_drawdown": float(backtest["max_drawdown"]),
                    "profit_factor": backtest["profit_factor"],
                    "trades": int(backtest["total_trades"]),
                    "blocked_by_trend": blocked_count,
                    "f1": float(walk_forward["metrics"]["f1"]),
                    "precision": float(walk_forward["metrics"]["precision"]),
                    "recall": float(walk_forward["metrics"]["recall"]),
                }
            )

    result = pd.DataFrame(rows).sort_values(
        by=["pnl", "profit_factor", "winrate"],
        ascending=[False, False, False],
        na_position="last",
    )
    return result.reset_index(drop=True)


def generate_signals(symbol: str, predictions: pd.DataFrame, *, trend_filter_mode: str) -> pd.DataFrame:
    items: list[dict[str, object]] = []
    for row in predictions.itertuples(index=False):
        signal_item = {
            "symbol": symbol,
            "probability": float(row.probability),
        }
        row_data = row._asdict()
        signal_direction = row_data.get("signal_direction")
        trend_direction = row_data.get("trend_direction")
        trend_strength = row_data.get("trend_strength")
        market_regime = row_data.get("market_regime")
        ema_20_distance = row_data.get("ema_20_distance")
        if pd.notna(signal_direction):
            signal_item["signal_direction"] = signal_direction
        if pd.notna(trend_direction):
            signal_item["trend_direction"] = trend_direction
        if pd.notna(trend_strength):
            signal_item["trend_strength"] = float(trend_strength)
        if pd.notna(market_regime):
            signal_item["market_regime"] = market_regime
        if pd.notna(ema_20_distance):
            signal_item["ema_20_distance"] = float(ema_20_distance)
        items.append(signal_item)

    payload = {
        "items": items,
        "buy_threshold": 0.0,
        "sell_threshold": 0.0,
        "trend_filter_mode": trend_filter_mode,
    }
    response = post_json(f"{STRATEGY_SERVICE_URL}/signals", payload)
    signals = pd.DataFrame(response["signals"])
    signal_columns = ["side", "confidence", "reason"]
    result = predictions.reset_index(drop=True).join(signals[signal_columns])
    return result


def evaluate_risk(symbol: str, signals: pd.DataFrame) -> dict[str, object] | None:
    if signals.empty:
        return None

    actionable = signals[signals["side"].isin(["BUY", "SELL"])]
    selected = actionable.iloc[-1] if not actionable.empty else signals.iloc[-1]
    atr = selected.get("atr")
    if pd.isna(atr) or float(atr) <= 0:
        atr = max(float(selected["high"]) - float(selected["low"]), float(selected["close"]) * 0.001)

    payload = {
        "symbol": symbol,
        "side": selected["side"],
        "confidence": float(selected["confidence"]),
        "account_equity": INITIAL_CAPITAL,
        "entry_price": float(selected["close"]),
        "atr": float(atr),
    }
    return post_json(f"{RISK_MANAGER_URL}/evaluate", payload)


def prepare_signals_for_backtest(signals: pd.DataFrame, *, probability_threshold: float) -> pd.DataFrame:
    if signals.empty or "timestamp" not in signals.columns:
        return signals

    signal_rows = signals.copy()
    signal_rows["timestamp"] = pd.to_datetime(signal_rows["timestamp"], utc=True)
    if signal_rows["timestamp"].duplicated().sum() == 0:
        return signal_rows.sort_values("timestamp").reset_index(drop=True)

    selected_rows: list[pd.Series] = []
    for _, group in signal_rows.sort_values("timestamp", kind="mergesort").groupby("timestamp", sort=True):
        actionable = group[
            group["side"].isin(["BUY", "SELL"])
            & (group["probability"].astype(float) > probability_threshold)
        ]
        if not actionable.empty:
            buy_rows = actionable[actionable["side"] == "BUY"]
            candidates = buy_rows if not buy_rows.empty else actionable
            selected_rows.append(candidates.sort_values("probability", ascending=False).iloc[0])
            continue

        if "signal_direction" in group.columns:
            long_rows = group[group["signal_direction"] == "long"]
        else:
            long_rows = pd.DataFrame()
        candidates = long_rows if not long_rows.empty else group
        selected_rows.append(candidates.iloc[0])

    return pd.DataFrame(selected_rows).sort_values("timestamp").reset_index(drop=True)


def run_backtest(
    signals: pd.DataFrame,
    *,
    probability_threshold: float,
    target_threshold: float,
    stop_loss_mode: str,
    atr_multiplier: float,
    risk_reward_ratio: float,
    horizon: int,
    cooldown_after_stop_loss: int = 0,
    cooldown_after_take_profit: int = 0,
    cooldown_after_time_exit: int = 0,
    rearm_probability_threshold: float | None = None,
) -> dict[str, object]:
    backtest_signals = prepare_signals_for_backtest(
        signals,
        probability_threshold=probability_threshold,
    )
    stop_loss_pct = max(target_threshold / 2, TAKER_FEE_RATE * 4)
    use_atr_stop = stop_loss_mode == "atr"
    candle_payload: list[dict[str, object]] = []
    for row in backtest_signals.itertuples(index=False):
        row_data = row._asdict()
        atr_value = row_data.get("atr")
        candle_payload.append(
            {
                "timestamp": row.timestamp.isoformat(),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
                "atr": None if atr_value is None or pd.isna(atr_value) else float(atr_value),
                "probability": float(row.probability),
                "side": row.side,
            }
        )

    payload = {
        "candles": candle_payload,
        "probability_threshold": probability_threshold,
        "initial_capital": INITIAL_CAPITAL,
        "position_size_fraction": 1.0,
        "stop_loss_mode": stop_loss_mode,
        "stop_loss_pct": stop_loss_pct,
        "atr_multiplier": atr_multiplier,
        "take_profit_pct": None if use_atr_stop else target_threshold,
        "take_profit_multiplier": risk_reward_ratio if use_atr_stop else 2.0,
        "max_holding_candles": horizon,
        "fee_rate": TAKER_FEE_RATE,
        "cooldown_after_stop_loss": cooldown_after_stop_loss,
        "cooldown_after_take_profit": cooldown_after_take_profit,
        "cooldown_after_time_exit": cooldown_after_time_exit,
        "rearm_probability_threshold": rearm_probability_threshold,
    }
    return post_json(f"{BACKTESTING_SERVICE_URL}/backtest", payload)


def run_walk_forward_window_backtests(
    *,
    walk_forward: dict[str, object],
    signals: pd.DataFrame,
    probability_threshold: float,
    target_threshold: float,
    stop_loss_mode: str,
    atr_multiplier: float,
    risk_reward_ratio: float,
    horizon: int,
    cooldown_after_stop_loss: int = 0,
    cooldown_after_take_profit: int = 0,
    cooldown_after_time_exit: int = 0,
    rearm_probability_threshold: float | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if signals.empty:
        return pd.DataFrame(rows)

    signal_rows = signals.copy()
    signal_rows["timestamp"] = pd.to_datetime(signal_rows["timestamp"], utc=True)

    for fold in walk_forward.get("folds", []):
        test_start = pd.to_datetime(fold.get("test_start"), utc=True)
        test_end = pd.to_datetime(fold.get("test_end"), utc=True)
        fold_signals = signal_rows[
            (signal_rows["timestamp"] >= test_start)
            & (signal_rows["timestamp"] <= test_end)
        ].copy()

        if len(fold_signals) < 2:
            rows.append(_empty_window_backtest_row(fold=fold))
            continue

        backtest = run_backtest(
            fold_signals,
            probability_threshold=probability_threshold,
            target_threshold=target_threshold,
            stop_loss_mode=stop_loss_mode,
            atr_multiplier=atr_multiplier,
            risk_reward_ratio=risk_reward_ratio,
            horizon=horizon,
            cooldown_after_stop_loss=cooldown_after_stop_loss,
            cooldown_after_take_profit=cooldown_after_take_profit,
            cooldown_after_time_exit=cooldown_after_time_exit,
            rearm_probability_threshold=rearm_probability_threshold,
        )
        profit_factor = backtest["profit_factor"]
        rows.append(
            {
                "fold": fold["fold"],
                "test_start": fold.get("test_start"),
                "test_end": fold.get("test_end"),
                "pnl": float(backtest["total_pnl"]),
                "return_pct": float(backtest["total_return_pct"]),
                "winrate": float(backtest["winrate"]),
                "max_drawdown": float(backtest["max_drawdown"]),
                "profit_factor": None if profit_factor is None else float(profit_factor),
                "trades": int(backtest["total_trades"]),
                "winning_trades": int(backtest["winning_trades"]),
                "losing_trades": int(backtest["losing_trades"]),
            }
        )

    return pd.DataFrame(rows)


def run_walk_forward_signal_diagnostics(
    *,
    walk_forward: dict[str, object],
    signals: pd.DataFrame,
    probability_threshold: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if signals.empty:
        return pd.DataFrame(rows)

    signal_rows = signals.copy()
    signal_rows["timestamp"] = pd.to_datetime(signal_rows["timestamp"], utc=True)

    for fold in walk_forward.get("folds", []):
        test_start = pd.to_datetime(fold.get("test_start"), utc=True)
        test_end = pd.to_datetime(fold.get("test_end"), utc=True)
        fold_signals = signal_rows[
            (signal_rows["timestamp"] >= test_start)
            & (signal_rows["timestamp"] <= test_end)
        ].copy()

        if fold_signals.empty:
            rows.append(_empty_signal_diagnostic_row(fold=fold))
            continue

        probabilities = pd.to_numeric(fold_signals["probability"], errors="coerce")
        above_entry = probabilities > probability_threshold
        below_entry = ~above_entry
        reasons = fold_signals.get("reason", pd.Series(index=fold_signals.index, dtype=object))
        sides = fold_signals.get("side", pd.Series(index=fold_signals.index, dtype=object))
        regimes = fold_signals.get("market_regime", pd.Series(index=fold_signals.index, dtype=object))
        trends = fold_signals.get("trend_direction", pd.Series(index=fold_signals.index, dtype=object))
        buy_signals = sides == "BUY"
        sell_signals = sides == "SELL"
        hold_signals = sides == "HOLD"
        blocked_by_trend = reasons == "blocked_by_trend_filter"

        rows.append(
            {
                "fold": fold["fold"],
                "test_start": fold.get("test_start"),
                "test_end": fold.get("test_end"),
                "predictions": int(len(fold_signals)),
                "above_entry": int(above_entry.sum()),
                "below_entry": int(below_entry.sum()),
                "buy_signals": int(buy_signals.sum()),
                "buy_above_entry": int((buy_signals & above_entry).sum()),
                "sell_signals": int(sell_signals.sum()),
                "sell_above_entry": int((sell_signals & above_entry).sum()),
                "hold_signals": int(hold_signals.sum()),
                "blocked_by_trend": int(blocked_by_trend.sum()),
                "blocked_above_entry": int((blocked_by_trend & above_entry).sum()),
                "max_probability": float(probabilities.max()) if probabilities.notna().any() else 0.0,
                "avg_probability": float(probabilities.mean()) if probabilities.notna().any() else 0.0,
                "trend_rows": int((regimes == "trend").sum()),
                "range_rows": int((regimes == "range").sum()),
                "high_vol_rows": int((regimes == "high_volatility").sum()),
                "up_trend_rows": int((trends == "up").sum()),
                "down_trend_rows": int((trends == "down").sum()),
                "flat_trend_rows": int((trends == "flat").sum()),
            }
        )

    return pd.DataFrame(rows)


def _empty_signal_diagnostic_row(*, fold: dict[str, object]) -> dict[str, object]:
    return {
        "fold": fold["fold"],
        "test_start": fold.get("test_start"),
        "test_end": fold.get("test_end"),
        "predictions": 0,
        "above_entry": 0,
        "below_entry": 0,
        "buy_signals": 0,
        "buy_above_entry": 0,
        "sell_signals": 0,
        "sell_above_entry": 0,
        "hold_signals": 0,
        "blocked_by_trend": 0,
        "blocked_above_entry": 0,
        "max_probability": 0.0,
        "avg_probability": 0.0,
        "trend_rows": 0,
        "range_rows": 0,
        "high_vol_rows": 0,
        "up_trend_rows": 0,
        "down_trend_rows": 0,
        "flat_trend_rows": 0,
    }


def _empty_window_backtest_row(*, fold: dict[str, object]) -> dict[str, object]:
    return {
        "fold": fold["fold"],
        "test_start": fold.get("test_start"),
        "test_end": fold.get("test_end"),
        "pnl": 0.0,
        "return_pct": 0.0,
        "winrate": 0.0,
        "max_drawdown": 0.0,
        "profit_factor": None,
        "trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
    }


def dataframe_to_candles(candles: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": float(row.volume),
        }
        for row in candles.itertuples(index=False)
    ]


def predictions_to_dataframe(training: dict[str, object]) -> pd.DataFrame:
    predictions = pd.DataFrame(training.get("predictions", []))
    if predictions.empty:
        return predictions

    predictions["timestamp"] = pd.to_datetime(predictions["timestamp"], utc=True)
    numeric_columns = ["open", "high", "low", "close", "volume", "probability", "confidence", "atr"]
    for column in numeric_columns:
        if column in predictions.columns:
            predictions[column] = pd.to_numeric(predictions[column], errors="coerce")
    return predictions


def create_price_figure(candles: pd.DataFrame, signals: pd.DataFrame | None) -> go.Figure:
    figure = go.Figure()
    if candles.empty:
        _apply_trading_layout(figure, height=540)
        return figure

    figure.add_trace(
        go.Candlestick(
            x=candles["timestamp"],
            open=candles["open"],
            high=candles["high"],
            low=candles["low"],
            close=candles["close"],
            increasing_line_color=COLOR_GREEN,
            increasing_fillcolor="rgba(0, 192, 135, 0.85)",
            decreasing_line_color=COLOR_RED,
            decreasing_fillcolor="rgba(246, 70, 93, 0.85)",
            name="Цена",
        )
    )

    if signals is not None and not signals.empty:
        buy_signals = signals[signals["side"] == "BUY"]
        sell_signals = signals[signals["side"] == "SELL"]
        figure.add_trace(
            go.Scatter(
                x=buy_signals["timestamp"],
                y=buy_signals["close"],
                mode="markers",
                marker={
                    "symbol": "triangle-up",
                    "size": 11,
                    "color": COLOR_GREEN,
                    "line": {"color": COLOR_BG, "width": 1},
                },
                name="Покупка",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=sell_signals["timestamp"],
                y=sell_signals["close"],
                mode="markers",
                marker={
                    "symbol": "triangle-down",
                    "size": 11,
                    "color": COLOR_RED,
                    "line": {"color": COLOR_BG, "width": 1},
                },
                name="Продажа",
            )
        )

    _apply_trading_layout(figure, height=540)
    return figure


def create_equity_figure(backtest: dict[str, object]) -> go.Figure:
    curve = pd.DataFrame(backtest.get("equity_curve", []))
    figure = go.Figure()
    if not curve.empty:
        figure.add_trace(
            go.Scatter(
                x=pd.to_datetime(curve["timestamp"], utc=True),
                y=curve["equity"],
                mode="lines",
                name="Капитал",
                line={"color": COLOR_GREEN, "width": 2},
            )
        )
    _apply_trading_layout(figure, height=340)
    return figure


def create_drawdown_figure(backtest: dict[str, object]) -> go.Figure:
    curve = pd.DataFrame(backtest.get("equity_curve", []))
    figure = go.Figure()
    if not curve.empty and "equity" in curve.columns:
        curve["timestamp"] = pd.to_datetime(curve["timestamp"], utc=True)
        equity = pd.to_numeric(curve["equity"], errors="coerce")
        peak = equity.cummax()
        drawdown = (equity / peak - 1).fillna(0.0)
        figure.add_trace(
            go.Scatter(
                x=curve["timestamp"],
                y=drawdown * 100,
                mode="lines",
                fill="tozeroy",
                name="Просадка",
                line={"color": COLOR_RED, "width": 2},
            )
        )
        figure.update_yaxes(ticksuffix="%")
    _apply_trading_layout(figure, height=260)
    return figure


def create_walk_forward_windows_figure(report: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    if not report.empty:
        rows = report.copy()
        colors = [COLOR_GREEN if float(value) >= 0 else COLOR_RED for value in rows["pnl"]]
        figure.add_trace(
            go.Bar(
                x=rows["fold"],
                y=rows["pnl"],
                marker_color=colors,
                name="PnL окна",
                hovertemplate="Окно %{x}<br>PnL: %{y:,.2f}<extra></extra>",
            )
        )
    _apply_trading_layout(figure, height=300)
    figure.update_xaxes(title_text="Окно")
    figure.update_yaxes(title_text="PnL")
    return figure


def trades_to_signal_points(trades: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    for trade in trades:
        side = trade.get("side")
        entry_time = trade.get("entry_timestamp")
        entry_price = trade.get("entry_price")
        if side is None or entry_time is None or entry_price is None:
            continue
        rows.append(
            {
                "timestamp": pd.to_datetime(entry_time, utc=True),
                "close": float(entry_price),
                "side": side,
            }
        )
    return pd.DataFrame(rows)


def _apply_trading_layout(figure: go.Figure, *, height: int) -> None:
    figure.update_layout(
        height=height,
        margin={"l": 34, "r": 66, "t": 26, "b": 34},
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        font={"color": COLOR_TEXT, "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif"},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "bgcolor": "rgba(0,0,0,0)",
        },
        xaxis={
            "gridcolor": "rgba(138, 150, 168, 0.12)",
            "linecolor": COLOR_BORDER,
            "tickfont": {"color": COLOR_MUTED},
            "rangeslider": {"visible": False},
            "automargin": True,
        },
        yaxis={
            "gridcolor": "rgba(138, 150, 168, 0.12)",
            "linecolor": COLOR_BORDER,
            "tickfont": {"color": COLOR_MUTED},
            "side": "right",
            "automargin": True,
        },
    )


def reset_after_data_change() -> None:
    st.session_state.training = None
    st.session_state.signals = pd.DataFrame()
    st.session_state.risk_decision = None
    st.session_state.backtest = None
    st.session_state.walk_forward = None
    st.session_state.walk_forward_signals = pd.DataFrame()
    st.session_state.walk_forward_backtest = None
    st.session_state.walk_forward_window_backtests = pd.DataFrame()
    st.session_state.walk_forward_signal_diagnostics = pd.DataFrame()
    st.session_state.walk_forward_grid = pd.DataFrame()
    st.session_state.walk_forward_grid_status = ""
    st.session_state.last_run_config = None


def translate_side(side: str) -> str:
    return {
        "BUY": "Покупка",
        "SELL": "Продажа",
        "HOLD": "Ожидание",
    }.get(side, side)


def translate_exit_reason(reason: object) -> str:
    return {
        "stop_loss": "Стоп",
        "take_profit": "Тейк",
        "time_exit": "Выход по времени",
    }.get(str(reason), str(reason))


def format_money(value: object) -> str:
    if pd.isna(value):
        return "-"
    return f"${float(value):,.2f}"


def format_date_value(value: object) -> str:
    if pd.isna(value):
        return "-"
    return pd.to_datetime(value, utc=True).strftime("%d/%m/%Y")


def format_datetime_value(value: object) -> str:
    if pd.isna(value):
        return "-"
    return pd.to_datetime(value, utc=True).strftime("%d/%m/%Y %H:%M")


def format_plain_number(value: object, *, digits: int = 2) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):,.{digits}f}"


def format_percentage(value: object) -> str:
    if pd.isna(value):
        return "-"
    numeric = float(value)
    if abs(numeric) <= 1:
        numeric *= 100
    return f"{numeric:.2f}%"


def format_probability(value: object) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.2f}"


def format_profit_factor(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.3f}"


def format_last_price(candles: pd.DataFrame) -> str:
    if candles.empty:
        return "-"
    return f"{float(candles.iloc[-1]['close']):,.4f}"


def format_price_change(candles: pd.DataFrame) -> tuple[str, str]:
    if len(candles) < 2:
        return "-", ""
    first_close = float(candles.iloc[0]["close"])
    last_close = float(candles.iloc[-1]["close"])
    if first_close == 0:
        return "-", ""
    change = (last_close / first_close) - 1
    css_class = "positive" if change >= 0 else "negative"
    return f"{change:.2%}", css_class


def format_backtest_pnl(backtest: dict[str, object] | None) -> tuple[str, str]:
    if backtest is None:
        return "-", ""
    pnl = float(backtest["total_pnl"])
    css_class = "positive" if pnl >= 0 else "negative"
    return format_money(pnl), css_class


def get_active_backtest() -> dict[str, object] | None:
    return st.session_state.walk_forward_backtest or st.session_state.backtest


def get_active_training() -> dict[str, object] | None:
    return st.session_state.walk_forward or st.session_state.training


def get_active_signals() -> pd.DataFrame:
    if not st.session_state.walk_forward_signals.empty:
        return st.session_state.walk_forward_signals
    return st.session_state.signals


def render_market_strip(
    *,
    symbol: str,
    timeframe: str,
    candles: pd.DataFrame,
    training: dict[str, object] | None,
    signals: pd.DataFrame,
    backtest: dict[str, object] | None,
) -> None:
    change_value, change_class = format_price_change(candles)
    pnl_value, pnl_class = format_backtest_pnl(backtest)
    signal_count = "-" if signals.empty else str(len(signals[signals["side"] != "HOLD"]))
    if training is None:
        test_rows = "-"
    else:
        test_rows = str(training.get("test_rows") or training.get("total_test_rows") or "-")

    st.markdown(
        f"""
        <div class="market-strip">
            <div class="market-card">
                <div class="market-label">Инструмент</div>
                <div class="market-value">{escape(symbol)}</div>
            </div>
            <div class="market-card">
                <div class="market-label">Таймфрейм</div>
                <div class="market-value">{escape(timeframe)}</div>
            </div>
            <div class="market-card">
                <div class="market-label">Последняя цена</div>
                <div class="market-value">{format_last_price(candles)}</div>
            </div>
            <div class="market-card">
                <div class="market-label">Изменение на выборке</div>
                <div class="market-value {change_class}">{change_value}</div>
            </div>
            <div class="market-card">
                <div class="market-label">Сигналы в тесте</div>
                <div class="market-value">{signal_count}</div>
            </div>
            <div class="market-card">
                <div class="market-label">PnL бэктеста</div>
                <div class="market-value {pnl_class}">{pnl_value}</div>
            </div>
        </div>
        <div class="brand-subtitle">Свечей: {len(candles)} · Тестовых строк: {test_rows}</div>
        """,
        unsafe_allow_html=True,
    )


def localize_signals(signals: pd.DataFrame) -> pd.DataFrame:
    table = signals.copy()
    if table.empty:
        return table
    table["side"] = table["side"].map(translate_side)
    if "trend_direction" in table.columns:
        table["trend_direction"] = table["trend_direction"].map(
            {
                "up": "Вверх",
                "down": "Вниз",
                "flat": "Боковик",
            }
        ).fillna("-")
    if "market_regime" in table.columns:
        table["market_regime"] = table["market_regime"].map(
            {
                "trend": "Тренд",
                "range": "Флэт",
                "high_volatility": "Высокая волатильность",
            }
        ).fillna("-")
    if "reason" in table.columns:
        table["reason"] = table["reason"].map(
            {
                "probability_and_trend": "Вероятность + тренд",
                "probability_below_threshold": "Ниже порога",
                "blocked_by_trend_filter": "Фильтр тренда",
            }
        ).fillna(table["reason"])
    return table.rename(
        columns={
            "timestamp": "Время",
            "close": "Цена",
            "probability": "Вероятность",
            "signal_direction": "Направление модели",
            "side": "Сигнал",
            "confidence": "Уверенность",
            "atr": "ATR",
            "ema_20_distance": "Отклонение от EMA20",
            "trend_direction": "Тренд",
            "market_regime": "Режим",
            "reason": "Причина",
        }
    )


def localize_trades(trades: list[dict[str, object]], *, compact: bool = False) -> pd.DataFrame:
    table = pd.DataFrame(trades)
    if table.empty:
        return table
    if "side" in table.columns:
        table["side"] = table["side"].map(translate_side)
    if "exit_reason" in table.columns:
        table["exit_reason"] = table["exit_reason"].map(translate_exit_reason)
    if compact:
        compact_columns = [
            column
            for column in [
                "entry_timestamp",
                "exit_timestamp",
                "side",
                "entry_price",
                "exit_price",
                "net_pnl",
                "return_pct",
                "exit_reason",
                "probability",
            ]
            if column in table.columns
        ]
        table = table[compact_columns]
    return table.rename(
        columns={
            "entry_timestamp": "Вход",
            "exit_timestamp": "Выход",
            "side": "Сторона",
            "entry_price": "Цена входа",
            "exit_price": "Цена выхода",
            "quantity": "Количество",
            "gross_pnl": "Грубый PnL",
            "fees": "Комиссии",
            "net_pnl": "Чистый PnL",
            "return_pct": "Доходность %",
            "exit_reason": "Причина выхода",
            "probability": "Вероятность",
        }
    )


def localize_walk_forward_folds(walk_forward: dict[str, object] | None) -> pd.DataFrame:
    if walk_forward is None:
        return pd.DataFrame()
    folds = pd.DataFrame(walk_forward.get("folds", []))
    if folds.empty:
        return folds

    metrics = pd.json_normalize(folds["metrics"])
    folds = pd.concat([folds.drop(columns=["metrics"]), metrics], axis=1)
    return folds.rename(
        columns={
            "fold": "Окно",
            "train_start": "Train start",
            "train_end": "Train end",
            "test_start": "Test start",
            "test_end": "Test end",
            "train_rows": "Train rows",
            "test_rows": "Test rows",
            "positive_rate": "Target=1",
            "accuracy": "Accuracy",
            "precision": "Precision",
            "recall": "Recall",
            "f1": "F1",
        }
    )


def localize_walk_forward_grid(grid: pd.DataFrame) -> pd.DataFrame:
    if grid.empty:
        return grid
    return grid.rename(
        columns={
            "target": "Target",
            "entry": "Entry",
            "pnl": "PnL",
            "return_pct": "Доходность",
            "winrate": "Winrate",
            "max_drawdown": "Просадка",
            "profit_factor": "Profit factor",
            "trades": "Сделки",
            "blocked_by_trend": "Отсечено трендом",
            "f1": "F1",
            "precision": "Precision",
            "recall": "Recall",
        }
    )


def localize_window_backtests(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty:
        return report
    return report.rename(
        columns={
            "fold": "Окно",
            "test_start": "Начало",
            "test_end": "Конец",
            "pnl": "PnL",
            "return_pct": "Доходность",
            "winrate": "Winrate",
            "max_drawdown": "Просадка",
            "profit_factor": "Profit factor",
            "trades": "Сделки",
            "winning_trades": "Плюсовые",
            "losing_trades": "Минусовые",
        }
    )


def localize_signal_diagnostics(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty:
        return report
    return report.rename(
        columns={
            "fold": "Окно",
            "test_start": "Начало",
            "test_end": "Конец",
            "predictions": "Прогнозов",
            "above_entry": "Выше entry",
            "below_entry": "Ниже entry",
            "buy_signals": "BUY",
            "buy_above_entry": "BUY выше entry",
            "sell_signals": "SELL",
            "sell_above_entry": "SELL выше entry",
            "hold_signals": "HOLD",
            "blocked_by_trend": "Отсечено трендом",
            "blocked_above_entry": "Отсечено выше entry",
            "max_probability": "Макс. вероятность",
            "avg_probability": "Средняя вероятность",
            "trend_rows": "Режим trend",
            "range_rows": "Режим range",
            "high_vol_rows": "High volatility",
            "up_trend_rows": "Тренд вверх",
            "down_trend_rows": "Тренд вниз",
            "flat_trend_rows": "Боковик",
        }
    )


def build_run_config(
    *,
    run_type: str,
    candles: pd.DataFrame,
    symbol: str,
    timeframe: str,
    history_months: int,
    history_end_date: date,
    history_start_date: date | None,
    horizon: int,
    target_threshold: float,
    probability_threshold: float,
    trade_mode: str,
    trend_filter_mode: str,
    feature_set: str,
    stop_loss_mode: str,
    atr_multiplier: float,
    risk_reward_ratio: float,
    train_window: int,
    test_window: int,
    max_folds: int,
    cooldown_after_stop_loss: int = 0,
    cooldown_after_take_profit: int = 0,
    cooldown_after_time_exit: int = 0,
    rearm_probability_threshold: float | None = None,
) -> dict[str, object]:
    candle_count = len(candles)
    first_candle = "-"
    last_candle = "-"
    if not candles.empty and "timestamp" in candles.columns:
        timestamps = pd.to_datetime(candles["timestamp"], utc=True)
        first_candle = format_datetime_value(timestamps.min())
        last_candle = format_datetime_value(timestamps.max())

    return {
        "Тип": run_type,
        "Инструмент": symbol,
        "Таймфрейм": timeframe,
        "История, мес.": history_months,
        "Дата начала": format_date_value(history_start_date) if history_start_date is not None else "-",
        "Дата окончания": format_date_value(history_end_date),
        "Свечей": candle_count,
        "Первая свеча": first_candle,
        "Последняя свеча": last_candle,
        "Target": target_threshold,
        "Entry": probability_threshold,
        "Горизонт": horizon,
        "Режим сделок": trade_mode,
        "Фильтр тренда": trend_filter_mode,
        "Признаки": feature_set,
        "SL/TP": stop_loss_mode,
        "ATR SL": atr_multiplier if stop_loss_mode == "atr" else "-",
        "Risk/Reward": risk_reward_ratio if stop_loss_mode == "atr" else "-",
        "Окно обучения": train_window,
        "Окно проверки": test_window,
        "Макс. окон": max_folds,
        "Cooldown после SL": cooldown_after_stop_loss,
        "Cooldown после TP": cooldown_after_take_profit,
        "Cooldown после time exit": cooldown_after_time_exit,
        "Re-arm probability": "-" if rearm_probability_threshold is None else rearm_probability_threshold,
    }


def render_run_config(config: dict[str, object] | None) -> None:
    if not config:
        return
    config_frame = pd.DataFrame(
        [{"Параметр": key, "Значение": value} for key, value in config.items()]
    )
    with st.expander("Параметры последнего запуска", expanded=False):
        render_dark_table(config_frame)


def build_config_summary(
    *,
    symbol: str,
    timeframe: str,
    candles: pd.DataFrame,
    horizon: int,
    target_threshold: float,
    probability_threshold: float,
    atr_multiplier: float,
    risk_reward_ratio: float,
) -> str:
    if candles.empty or "timestamp" not in candles.columns:
        date_range = "данные не загружены"
    else:
        timestamps = pd.to_datetime(candles["timestamp"], utc=True)
        date_range = f"{format_date_value(timestamps.min())} - {format_date_value(timestamps.max())}"
    return (
        f"{symbol} · {timeframe} · {date_range} · "
        f"horizon {horizon} · target {target_threshold:.3f} · "
        f"entry {probability_threshold:.2f} · ATR {atr_multiplier:.2f} · RR {risk_reward_ratio:.2f}"
    )


def render_overview_metrics(
    *,
    backtest: dict[str, object] | None,
    window_report: pd.DataFrame,
) -> None:
    metric_cols = st.columns(6)
    if backtest is None:
        metric_cols[0].metric("PnL", "-", help="Итоговый чистый результат бэктеста после комиссий.")
        metric_cols[1].metric("Profit Factor", "-", help="Отношение суммы прибыльных сделок к сумме убыточных.")
        metric_cols[2].metric("Max Drawdown", "-", help="Максимальная просадка капитала от локального пика.")
        metric_cols[3].metric("Winrate", "-")
        metric_cols[4].metric("Trades", "-")
    else:
        metric_cols[0].metric(
            "PnL",
            format_money(backtest["total_pnl"]),
            help="Итоговый чистый результат бэктеста после комиссий.",
        )
        metric_cols[1].metric(
            "Profit Factor",
            format_profit_factor(backtest.get("profit_factor")),
            help="Отношение суммы прибыльных сделок к сумме убыточных. Значение выше 1 означает прибыльную выборку.",
        )
        metric_cols[2].metric(
            "Max Drawdown",
            format_percentage(backtest["max_drawdown"]),
            help="Максимальная просадка капитала от локального пика.",
        )
        metric_cols[3].metric("Winrate", format_percentage(backtest["winrate"]))
        metric_cols[4].metric("Trades", int(backtest.get("total_trades", 0)))

    if window_report.empty:
        metric_cols[5].metric("Positive Windows", "-")
    else:
        positive_windows = int((window_report["pnl"] > 0).sum())
        metric_cols[5].metric("Positive Windows", f"{positive_windows}/{len(window_report)}")


def render_demo_metric_notes() -> None:
    note_cols = st.columns(4)
    note_cols[0].caption("PnL: чистая прибыль или убыток стратегии после комиссий.")
    note_cols[1].caption("Profit Factor: насколько прибыльные сделки перекрывают убыточные.")
    note_cols[2].caption("Max Drawdown: худшая просадка equity curve от пика.")
    note_cols[3].caption("Walk-forward: проверка модели на последовательных будущих окнах без перемешивания данных.")


def localize_worst_windows(report: pd.DataFrame, *, limit: int = 8) -> pd.DataFrame:
    if report.empty:
        return report
    columns = ["fold", "test_start", "test_end", "pnl", "return_pct", "max_drawdown", "trades"]
    rows = report.sort_values("pnl", ascending=True).head(limit)
    return localize_window_backtests(rows[[column for column in columns if column in rows.columns]])


def render_dark_table(dataframe: pd.DataFrame, *, empty_text: str = "Нет данных") -> None:
    if dataframe.empty:
        st.markdown(f'<div class="dark-table-empty">{escape(empty_text)}</div>', unsafe_allow_html=True)
        return

    table = dataframe.copy()
    for column in table.columns:
        table[column] = table[column].map(lambda value, column=column: format_table_cell(value, column=column))

    numeric_columns = {
        column
        for column in dataframe.columns
        if pd.api.types.is_numeric_dtype(dataframe[column])
    }
    header_html = "".join(f"<th>{escape(str(column))}</th>" for column in table.columns)
    body_rows = []
    for _, row in table.iterrows():
        cells = []
        for column, value in row.items():
            css_class = ' class="num"' if column in numeric_columns else ""
            cells.append(f"<td{css_class}>{escape(str(value))}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    st.markdown(
        f"""
        <div class="dark-table-wrap">
            <table class="dark-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(body_rows)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_table_cell(value: object, *, column: str | None = None) -> str:
    if pd.isna(value):
        return "-"
    if isinstance(value, pd.Timestamp):
        return format_datetime_value(value)
    if column:
        if column in DATE_COLUMNS:
            try:
                return format_datetime_value(value)
            except (TypeError, ValueError):
                return str(value)
        if column in MONEY_COLUMNS:
            return format_money(value)
        if column in PERCENT_COLUMNS:
            return format_percentage(value)
        if column in PROBABILITY_COLUMNS:
            return format_probability(value)
        if column in PRICE_COLUMNS:
            return format_plain_number(value, digits=2)
        if column.lower() == "profit factor":
            return format_profit_factor(value)
    if isinstance(value, float):
        if abs(value) >= 100:
            return f"{value:,.2f}"
        return f"{value:.4f}"
    return str(value)


st.set_page_config(page_title="Алготрейдинг", layout="wide")
inject_theme()


def render_empty_state(title: str, description: str | None = None) -> None:
    message = escape(title)
    if description is not None:
        message = f"{message}<br><span>{escape(description)}</span>"
    st.markdown(f'<div class="dark-table-empty">{message}</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="trading-header">
        <div class="brand-wrap">
            <div class="brand-mark">AT</div>
            <div>
                <div class="brand-title">Панель алгоритмической торговли</div>
                <div class="brand-subtitle">Фьючерсы · машинное обучение · риск-менеджмент · бэктест</div>
            </div>
        </div>
        <div class="header-actions">
            <div class="mode-pill">Режим: бумажная торговля</div>
            <div class="status-pill">REST-сервисы</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Demo-параметры")
    demo_mode = st.toggle("Demo mode", value=True, key="demo_mode_v3")
    if demo_mode:
        st.caption("Режим защиты: только основной сценарий и итоговые результаты.")
    else:
        st.caption("Research mode: дополнительные настройки, сигналы и подбор параметров.")
    symbol = st.selectbox("Инструмент", ["SOL-USDT", "BTC-USDT"], index=1, key="symbol_v3")
    timeframe = st.selectbox("Таймфрейм", ["5m", "15m", "30m", "1h", "4h"], index=4, key="timeframe_v3")
    history_months = 24
    history_range_mode = "fixed_start"
    history_start_date: date | None = date(2024, 4, 19)
    history_end_date = DEFAULT_LONG_HISTORY_END_DATE
    train_clicked = False
    backtest_clicked = False
    walk_forward_grid_clicked = False

    with st.expander("Данные", expanded=True):
        history_end_date = st.date_input(
            "Дата окончания истории",
            value=DEFAULT_LONG_HISTORY_END_DATE,
            max_value=DEFAULT_TODAY,
            key="history_end_date_v3",
        )
        history_range_mode = st.radio(
            "Диапазон истории",
            ["rolling", "fixed_start"],
            format_func=lambda value: {
                "rolling": "Последние N месяцев",
                "fixed_start": "Фиксированная дата начала",
            }[value],
            horizontal=True,
            index=1,
            key="history_range_mode_v3",
        )
        if history_range_mode == "rolling":
            history_months = st.slider("История, месяцев", min_value=1, max_value=24, value=24, key="history_months_v3")
            history_start_date = None
            estimated_candles = estimate_candle_count(timeframe=timeframe, history_months=int(history_months))
        else:
            history_start_date = st.date_input(
                "Дата начала истории",
                value=date(2024, 4, 19),
                max_value=history_end_date,
                key="history_start_date_v3",
            )
            estimated_candles = estimate_candle_count_for_dates(
                timeframe=timeframe,
                start_date=history_start_date,
                end_date=history_end_date,
            )
            st.caption("Сравнение разных дат окончания честное: начало истории не сдвигается.")
        st.caption(f"Оценка: около {estimated_candles:,} свечей")

    with st.expander("Модель", expanded=True):
        horizon = st.number_input("Горизонт прогноза", min_value=1, max_value=48, value=4, key="horizon_v3")
        target_threshold = st.number_input(
            "Порог роста для target",
            min_value=0.001,
            max_value=0.05,
            value=0.010,
            step=0.001,
            format="%.3f",
            key="target_threshold_v3",
        )
        probability_threshold = st.slider(
            "Порог входа",
            min_value=0.30,
            max_value=0.95,
            value=0.56,
            step=0.01,
            key="probability_threshold_v3",
        )
        feature_set = "v2"

    with st.expander("Бэктест", expanded=True):
        stop_loss_mode = st.selectbox(
            "SL/TP",
            ["fixed", "atr"],
            format_func=lambda value: {
                "fixed": "Фиксированный",
                "atr": "По ATR",
            }[value],
            index=1,
            key="stop_loss_mode_v3",
        )
        atr_multiplier = st.number_input("ATR множитель SL", min_value=0.5, max_value=5.0, value=1.5, step=0.25, key="atr_multiplier_v3")
        risk_reward_ratio = st.number_input("Risk/Reward", min_value=1.0, max_value=5.0, value=2.0, step=0.25, key="risk_reward_ratio_v3")
        if stop_loss_mode == "atr":
            st.caption("SL = ATR * множитель, TP = SL * Risk/Reward, выход по времени = horizon")
        else:
            st.caption("TP = target, SL = target / 2, выход по времени = horizon")

    with st.expander("Walk-forward", expanded=False):
        if timeframe == "1h":
            default_train_window = 2400
            default_test_window = 480
            default_max_folds = 30
        elif timeframe == "4h":
            default_train_window = 600
            default_test_window = 120
            default_max_folds = 35
        else:
            default_train_window = 1200
            default_test_window = 240
            default_max_folds = 12
        train_window = st.number_input("Окно обучения", min_value=100, max_value=5000, value=default_train_window, step=100, key=f"train_window_{timeframe}_v3")
        test_window = st.number_input("Окно проверки", min_value=20, max_value=1000, value=default_test_window, step=20, key=f"test_window_{timeframe}_v3")
        max_folds = st.number_input("Максимум окон", min_value=1, max_value=50, value=default_max_folds, step=1, key=f"max_folds_{timeframe}_v3")
        required_wf_rows = estimate_walk_forward_required_rows(
            train_window=int(train_window),
            test_window=int(test_window),
            feature_set=feature_set,
            horizon=int(horizon),
        )
        estimated_max_folds = estimate_walk_forward_max_folds(
            estimated_rows=estimated_candles,
            train_window=int(train_window),
            test_window=int(test_window),
            feature_set=feature_set,
            horizon=int(horizon),
        )
        estimated_coverage_days = estimate_walk_forward_coverage_days(
            timeframe=timeframe,
            test_window=int(test_window),
            max_folds=int(max_folds),
        )
        st.caption(f"Минимум для WF: около {required_wf_rows:,} свечей")
        st.caption(
            f"Доступно до {estimated_max_folds} окон; текущий тест покрывает около {estimated_coverage_days:.0f} дней."
        )

    trade_mode = "long_only"
    trend_filter_mode = "soft"
    if not demo_mode:
        with st.expander("Advanced / Research", expanded=False):
            trade_mode = st.selectbox(
                "Режим сделок",
                ["long_only", "short_only", "long_short"],
                format_func=lambda value: {
                    "long_only": "Только Long",
                    "short_only": "Только Short (исследование)",
                    "long_short": "Long + Short (исследование)",
                }[value],
                index=0,
            )
            trend_filter_mode = st.selectbox(
                "Фильтр тренда",
                ["strict", "soft", "off"],
                format_func=lambda value: {
                    "strict": "Строгий",
                    "soft": "Мягкий",
                    "off": "Выключен",
                }[value],
                index=1,
            )
            feature_set = st.selectbox("Набор признаков", ["baseline", "v2"], index=1)
            grid_target_values, grid_entry_values = get_walk_forward_grid_ranges(timeframe=timeframe, trade_mode=trade_mode)
            st.caption(
                "WF-grid: "
                f"target {', '.join(f'{value:.3f}' for value in grid_target_values)}; "
                f"entry {', '.join(f'{value:.2f}' for value in grid_entry_values)}"
            )
            st.caption("Подбор параметров нужен только для исследования, не для финальной оценки стратегии.")

    cooldown_after_stop_loss = 0
    cooldown_after_take_profit = 0
    cooldown_after_time_exit = 0
    rearm_probability_threshold: float | None = None
    if timeframe == "1h" and not demo_mode:
        with st.expander("1h anti-noise", expanded=False):
            use_1h_cooldown = st.checkbox("Cooldown", value=False)
            use_1h_rearm = st.checkbox("Re-arm", value=False)
            cooldown_disabled = not use_1h_cooldown
            guard_cols = st.columns(3)
            cooldown_after_stop_loss = int(
                guard_cols[0].number_input(
                    "CD после SL",
                    min_value=0,
                    max_value=48,
                    value=3,
                    step=1,
                    disabled=cooldown_disabled,
                )
            )
            cooldown_after_take_profit = int(
                guard_cols[1].number_input(
                    "CD после TP",
                    min_value=0,
                    max_value=24,
                    value=0,
                    step=1,
                    disabled=cooldown_disabled,
                )
            )
            cooldown_after_time_exit = int(
                guard_cols[2].number_input(
                    "CD после time",
                    min_value=0,
                    max_value=48,
                    value=0,
                    step=1,
                    disabled=cooldown_disabled,
                )
            )
            rearm_probability_threshold = float(
                st.number_input(
                    "Re-arm ниже вероятности",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.55,
                    step=0.01,
                    disabled=not use_1h_rearm,
                )
            )
            if cooldown_disabled:
                cooldown_after_stop_loss = 0
                cooldown_after_take_profit = 0
                cooldown_after_time_exit = 0
            if not use_1h_rearm:
                rearm_probability_threshold = None
            st.caption("Опциональная защита от серийных входов на шумном 1h.")
    elif timeframe != "1h" and not demo_mode:
        st.caption("Cooldown/re-arm скрыты: для 4h и выше шумовой фильтр обычно не нужен.")

    load_clicked = st.button("Загрузить данные", use_container_width=True)
    walk_forward_clicked = st.button("Запустить walk-forward", use_container_width=True)
    if demo_mode:
        st.caption("Основной сценарий: загрузите данные, затем запустите walk-forward.")
    else:
        with st.expander("Дополнительные действия", expanded=False):
            train_clicked = st.button("Обучить модель", use_container_width=True)
            backtest_clicked = st.button("Запустить бэктест", use_container_width=True)
            walk_forward_grid_clicked = st.button("Подбор WF-параметров", use_container_width=True)

if "candles" not in st.session_state:
    st.session_state.candles = pd.DataFrame()
if "training" not in st.session_state:
    st.session_state.training = None
if "signals" not in st.session_state:
    st.session_state.signals = pd.DataFrame()
if "risk_decision" not in st.session_state:
    st.session_state.risk_decision = None
if "backtest" not in st.session_state:
    st.session_state.backtest = None
if "walk_forward" not in st.session_state:
    st.session_state.walk_forward = None
if "walk_forward_signals" not in st.session_state:
    st.session_state.walk_forward_signals = pd.DataFrame()
if "walk_forward_backtest" not in st.session_state:
    st.session_state.walk_forward_backtest = None
if "walk_forward_window_backtests" not in st.session_state:
    st.session_state.walk_forward_window_backtests = pd.DataFrame()
if "walk_forward_signal_diagnostics" not in st.session_state:
    st.session_state.walk_forward_signal_diagnostics = pd.DataFrame()
if "walk_forward_grid" not in st.session_state:
    st.session_state.walk_forward_grid = pd.DataFrame()
if "walk_forward_grid_status" not in st.session_state:
    st.session_state.walk_forward_grid_status = ""
if "last_run_config" not in st.session_state:
    st.session_state.last_run_config = None

if load_clicked:
    with st.spinner("Загружаем рыночные данные"):
        try:
            st.session_state.candles = fetch_market_data(
                symbol=symbol,
                timeframe=timeframe,
                history_months=int(history_months),
                history_end_date=history_end_date,
                history_start_date=history_start_date,
            )
            reset_after_data_change()
        except Exception as exc:
            st.error(f"Не удалось загрузить данные: {exc}")

if train_clicked:
    if st.session_state.candles.empty:
        st.warning("Сначала загрузите данные.")
    else:
        with st.spinner("Обучаем модель и формируем сигналы"):
            try:
                st.session_state.training = train_model(
                    st.session_state.candles,
                    symbol=symbol,
                    horizon=int(horizon),
                    threshold=float(target_threshold),
                    feature_set=feature_set,
                    target_direction="short" if trade_mode == "short_only" else "long",
                )
                predictions = predictions_to_dataframe(st.session_state.training)
                predictions["signal_direction"] = "short" if trade_mode == "short_only" else "long"
                st.session_state.signals = generate_signals(
                    symbol=symbol,
                    predictions=predictions,
                    trend_filter_mode=trend_filter_mode,
                )
                st.session_state.risk_decision = evaluate_risk(symbol=symbol, signals=st.session_state.signals)
                st.session_state.backtest = None
                st.session_state.walk_forward = None
                st.session_state.walk_forward_signals = pd.DataFrame()
                st.session_state.walk_forward_backtest = None
                st.session_state.walk_forward_window_backtests = pd.DataFrame()
                st.session_state.walk_forward_signal_diagnostics = pd.DataFrame()
                st.session_state.walk_forward_grid = pd.DataFrame()
            except Exception as exc:
                st.error(f"Не удалось обучить модель или сформировать сигналы: {exc}")

if backtest_clicked:
    signals_for_backtest = get_active_signals()
    if signals_for_backtest.empty:
        st.warning("Сначала обучите модель или запустите walk-forward тест.")
    else:
        with st.spinner("Запускаем бэктест"):
            try:
                st.session_state.backtest = run_backtest(
                    signals_for_backtest,
                    probability_threshold=float(probability_threshold),
                    target_threshold=float(target_threshold),
                    stop_loss_mode=stop_loss_mode,
                    atr_multiplier=float(atr_multiplier),
                    risk_reward_ratio=float(risk_reward_ratio),
                    horizon=int(horizon),
                    cooldown_after_stop_loss=int(cooldown_after_stop_loss),
                    cooldown_after_take_profit=int(cooldown_after_take_profit),
                    cooldown_after_time_exit=int(cooldown_after_time_exit),
                    rearm_probability_threshold=rearm_probability_threshold,
                )
                st.session_state.last_run_config = build_run_config(
                    run_type="Обычный бэктест",
                    candles=st.session_state.candles,
                    symbol=symbol,
                    timeframe=timeframe,
                    history_months=int(history_months),
                    history_end_date=history_end_date,
                    history_start_date=history_start_date,
                    horizon=int(horizon),
                    target_threshold=float(target_threshold),
                    probability_threshold=float(probability_threshold),
                    trade_mode=trade_mode,
                    trend_filter_mode=trend_filter_mode,
                    feature_set=feature_set,
                    stop_loss_mode=stop_loss_mode,
                    atr_multiplier=float(atr_multiplier),
                    risk_reward_ratio=float(risk_reward_ratio),
                    train_window=int(train_window),
                    test_window=int(test_window),
                    max_folds=int(max_folds),
                    cooldown_after_stop_loss=int(cooldown_after_stop_loss),
                    cooldown_after_take_profit=int(cooldown_after_take_profit),
                    cooldown_after_time_exit=int(cooldown_after_time_exit),
                    rearm_probability_threshold=rearm_probability_threshold,
                )
                if int(st.session_state.backtest.get("total_trades", 0)) == 0:
                    st.warning(
                        "Бэктест не открыл сделок: в активном наборе сигналов нет BUY/SELL "
                        "выше текущего порога входа, либо все входы отфильтрованы трендом."
                    )
            except Exception as exc:
                st.error(f"Не удалось запустить бэктест: {exc}")

if walk_forward_clicked:
    if st.session_state.candles.empty:
        st.warning("Сначала загрузите данные.")
    else:
        enough_rows, loaded_rows, required_rows = has_enough_rows_for_walk_forward(
            st.session_state.candles,
            train_window=int(train_window),
            test_window=int(test_window),
            feature_set=feature_set,
            horizon=int(horizon),
        )
        if not enough_rows:
            st.warning(
                "Недостаточно свечей для walk-forward: "
                f"загружено {loaded_rows:,}, нужно примерно {required_rows:,}. "
                "Увеличьте историю данных или уменьшите окно обучения/проверки."
            )
            st.stop()
        with st.spinner("Запускаем walk-forward проверку"):
            try:
                st.session_state.walk_forward, predictions = build_mode_predictions(
                    candles=st.session_state.candles,
                    symbol=symbol,
                    horizon=int(horizon),
                    threshold=float(target_threshold),
                    feature_set=feature_set,
                    trade_mode=trade_mode,
                    train_window=int(train_window),
                    test_window=int(test_window),
                    step_size=int(test_window),
                    max_folds=int(max_folds),
                )
                st.session_state.walk_forward_signals = generate_signals(
                    symbol=symbol,
                    predictions=predictions,
                    trend_filter_mode=trend_filter_mode,
                )
                st.session_state.risk_decision = evaluate_risk(
                    symbol=symbol,
                    signals=st.session_state.walk_forward_signals,
                )
                st.session_state.walk_forward_backtest = run_backtest(
                    st.session_state.walk_forward_signals,
                    probability_threshold=float(probability_threshold),
                    target_threshold=float(target_threshold),
                    stop_loss_mode=stop_loss_mode,
                    atr_multiplier=float(atr_multiplier),
                    risk_reward_ratio=float(risk_reward_ratio),
                    horizon=int(horizon),
                    cooldown_after_stop_loss=int(cooldown_after_stop_loss),
                    cooldown_after_take_profit=int(cooldown_after_take_profit),
                    cooldown_after_time_exit=int(cooldown_after_time_exit),
                    rearm_probability_threshold=rearm_probability_threshold,
                )
                st.session_state.walk_forward_window_backtests = run_walk_forward_window_backtests(
                    walk_forward=st.session_state.walk_forward,
                    signals=st.session_state.walk_forward_signals,
                    probability_threshold=float(probability_threshold),
                    target_threshold=float(target_threshold),
                    stop_loss_mode=stop_loss_mode,
                    atr_multiplier=float(atr_multiplier),
                    risk_reward_ratio=float(risk_reward_ratio),
                    horizon=int(horizon),
                    cooldown_after_stop_loss=int(cooldown_after_stop_loss),
                    cooldown_after_take_profit=int(cooldown_after_take_profit),
                    cooldown_after_time_exit=int(cooldown_after_time_exit),
                    rearm_probability_threshold=rearm_probability_threshold,
                )
                st.session_state.walk_forward_signal_diagnostics = run_walk_forward_signal_diagnostics(
                    walk_forward=st.session_state.walk_forward,
                    signals=st.session_state.walk_forward_signals,
                    probability_threshold=float(probability_threshold),
                )
                st.session_state.last_run_config = build_run_config(
                    run_type="Walk-forward",
                    candles=st.session_state.candles,
                    symbol=symbol,
                    timeframe=timeframe,
                    history_months=int(history_months),
                    history_end_date=history_end_date,
                    history_start_date=history_start_date,
                    horizon=int(horizon),
                    target_threshold=float(target_threshold),
                    probability_threshold=float(probability_threshold),
                    trade_mode=trade_mode,
                    trend_filter_mode=trend_filter_mode,
                    feature_set=feature_set,
                    stop_loss_mode=stop_loss_mode,
                    atr_multiplier=float(atr_multiplier),
                    risk_reward_ratio=float(risk_reward_ratio),
                    train_window=int(train_window),
                    test_window=int(test_window),
                    max_folds=int(max_folds),
                    cooldown_after_stop_loss=int(cooldown_after_stop_loss),
                    cooldown_after_take_profit=int(cooldown_after_take_profit),
                    cooldown_after_time_exit=int(cooldown_after_time_exit),
                    rearm_probability_threshold=rearm_probability_threshold,
                )
            except Exception as exc:
                st.error(f"Не удалось выполнить walk-forward test: {exc}")

if walk_forward_grid_clicked:
    if st.session_state.candles.empty:
        st.warning("Сначала загрузите данные.")
    else:
        enough_rows, loaded_rows, required_rows = has_enough_rows_for_walk_forward(
            st.session_state.candles,
            train_window=int(train_window),
            test_window=int(test_window),
            feature_set=feature_set,
            horizon=int(horizon),
        )
        if not enough_rows:
            st.warning(
                "Недостаточно свечей для подбора WF-параметров: "
                f"загружено {loaded_rows:,}, нужно примерно {required_rows:,}. "
                "Увеличьте историю данных или уменьшите окно обучения/проверки."
            )
            st.stop()
        st.session_state.walk_forward_grid_status = "Подбор выполняется..."
        with st.spinner("Подбираем параметры через walk-forward"):
            try:
                st.session_state.walk_forward_grid = run_walk_forward_grid(
                    st.session_state.candles,
                    symbol=symbol,
                    timeframe=timeframe,
                    horizon=int(horizon),
                    feature_set=feature_set,
                    trade_mode=trade_mode,
                    trend_filter_mode=trend_filter_mode,
                    stop_loss_mode=stop_loss_mode,
                    atr_multiplier=float(atr_multiplier),
                    risk_reward_ratio=float(risk_reward_ratio),
                    train_window=int(train_window),
                    test_window=int(test_window),
                    step_size=int(test_window),
                    max_folds=int(max_folds),
                    cooldown_after_stop_loss=int(cooldown_after_stop_loss),
                    cooldown_after_take_profit=int(cooldown_after_take_profit),
                    cooldown_after_time_exit=int(cooldown_after_time_exit),
                    rearm_probability_threshold=rearm_probability_threshold,
                )
                best_row = st.session_state.walk_forward_grid.iloc[0]
                st.session_state.walk_forward_grid_status = (
                    f"Готово: лучший target {best_row['target']:.3f}, "
                    f"entry {best_row['entry']:.2f}, PnL {best_row['pnl']:,.2f}"
                )
                st.session_state.last_run_config = build_run_config(
                    run_type="Подбор WF-параметров",
                    candles=st.session_state.candles,
                    symbol=symbol,
                    timeframe=timeframe,
                    history_months=int(history_months),
                    history_end_date=history_end_date,
                    history_start_date=history_start_date,
                    horizon=int(horizon),
                    target_threshold=float(target_threshold),
                    probability_threshold=float(probability_threshold),
                    trade_mode=trade_mode,
                    trend_filter_mode=trend_filter_mode,
                    feature_set=feature_set,
                    stop_loss_mode=stop_loss_mode,
                    atr_multiplier=float(atr_multiplier),
                    risk_reward_ratio=float(risk_reward_ratio),
                    train_window=int(train_window),
                    test_window=int(test_window),
                    max_folds=int(max_folds),
                    cooldown_after_stop_loss=int(cooldown_after_stop_loss),
                    cooldown_after_take_profit=int(cooldown_after_take_profit),
                    cooldown_after_time_exit=int(cooldown_after_time_exit),
                    rearm_probability_threshold=rearm_probability_threshold,
                )
                st.success(st.session_state.walk_forward_grid_status)
            except Exception as exc:
                st.session_state.walk_forward_grid_status = f"Ошибка подбора: {exc}"
                st.error(f"Не удалось выполнить подбор параметров: {exc}")

candles = st.session_state.candles
training = get_active_training()
signals = get_active_signals()
risk_decision = st.session_state.risk_decision
backtest = get_active_backtest()
walk_forward = st.session_state.walk_forward
walk_forward_window_backtests = st.session_state.walk_forward_window_backtests
walk_forward_signal_diagnostics = st.session_state.walk_forward_signal_diagnostics
walk_forward_grid = st.session_state.walk_forward_grid
walk_forward_grid_status = st.session_state.walk_forward_grid_status
last_run_config = st.session_state.last_run_config

render_market_strip(
    symbol=symbol,
    timeframe=timeframe,
    candles=candles,
    training=training,
    signals=signals,
    backtest=backtest,
)

if walk_forward_grid_status and not demo_mode:
    st.info(walk_forward_grid_status)

if not demo_mode:
    render_run_config(last_run_config)

tab_names = ["Обзор", "Walk-forward", "Сделки", "Модель", "Сервисы"]
if not demo_mode:
    tab_names.insert(3, "Сигналы")
tabs = dict(zip(tab_names, st.tabs(tab_names), strict=True))
overview_tab = tabs["Обзор"]
walk_forward_tab = tabs["Walk-forward"]
trades_tab = tabs["Сделки"]
model_tab = tabs["Модель"]
service_tab = tabs["Сервисы"]
signals_tab = tabs.get("Сигналы")

with overview_tab:
    st.markdown('<div class="section-title">Обзор стратегии</div>', unsafe_allow_html=True)
    st.caption(
        build_config_summary(
            symbol=symbol,
            timeframe=timeframe,
            candles=candles,
            horizon=int(horizon),
            target_threshold=float(target_threshold),
            probability_threshold=float(probability_threshold),
            atr_multiplier=float(atr_multiplier),
            risk_reward_ratio=float(risk_reward_ratio),
        )
    )
    st.caption("Торговые метрики показывают результат стратегии с учетом фильтров, SL/TP, комиссий и выхода по времени.")
    render_overview_metrics(backtest=backtest, window_report=walk_forward_window_backtests)
    if demo_mode:
        render_demo_metric_notes()

    if candles.empty:
        render_empty_state(
            "Сначала загрузите данные",
            "После загрузки здесь появятся equity curve, drawdown и таблицы сделок.",
        )
    elif backtest is None:
        render_empty_state(
            "Сначала запустите walk-forward",
            "Dashboard покажет торговые метрики, equity curve, drawdown и сделки.",
        )
    else:
        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.markdown('<div class="section-title">Equity curve</div>', unsafe_allow_html=True)
            st.plotly_chart(create_equity_figure(backtest), use_container_width=True, key="overview_equity_curve")
        with chart_cols[1]:
            st.markdown('<div class="section-title">Drawdown curve</div>', unsafe_allow_html=True)
            st.plotly_chart(create_drawdown_figure(backtest), use_container_width=True, key="overview_drawdown_curve")

    st.markdown('<div class="section-title">График цены</div>', unsafe_allow_html=True)
    signal_display_mode = st.radio(
        "Отображение маркеров",
        ["only_trades", "all_signals"],
        format_func=lambda value: {
            "only_trades": "Только сделки",
            "all_signals": "Все сигналы",
        }[value],
        horizontal=True,
        label_visibility="collapsed",
    )
    if signal_display_mode == "only_trades" and backtest is not None:
        chart_signals = trades_to_signal_points(backtest.get("trades", []))
    else:
        chart_signals = signals
    if candles.empty:
        render_empty_state("Сначала загрузите данные", "График цены появится после получения свечей.")
    else:
        st.plotly_chart(
            create_price_figure(candles, None if chart_signals.empty else chart_signals),
            use_container_width=True,
            key=f"overview_price_{signal_display_mode}",
        )

    overview_cols = st.columns(2)
    with overview_cols[0]:
        st.markdown('<div class="section-title">Последние 20 сделок</div>', unsafe_allow_html=True)
        if backtest is None:
            render_empty_state("Нет сделок для отображения", "Запустите walk-forward, чтобы сформировать бэктест.")
        else:
            render_dark_table(
                localize_trades(backtest.get("trades", []), compact=True).tail(20),
                empty_text="Нет сделок для отображения.",
            )
    with overview_cols[1]:
        st.markdown('<div class="section-title">Худшие walk-forward окна</div>', unsafe_allow_html=True)
        if walk_forward_window_backtests.empty:
            render_empty_state("Сначала запустите walk-forward", "После проверки здесь появятся худшие окна.")
        else:
            render_dark_table(
                localize_worst_windows(walk_forward_window_backtests, limit=8),
                empty_text="Нет окон для отображения.",
            )

    st.markdown('<div class="section-title">PnL по walk-forward окнам</div>', unsafe_allow_html=True)
    if walk_forward_window_backtests.empty:
        render_empty_state("Сначала запустите walk-forward", "График PnL по окнам появится после проверки.")
    else:
        st.plotly_chart(
            create_walk_forward_windows_figure(walk_forward_window_backtests),
            use_container_width=True,
            key="overview_walk_forward_windows",
        )

with model_tab:
    st.markdown('<div class="section-title">ML-метрики</div>', unsafe_allow_html=True)
    st.caption("ML-метрики показывают качество классификации target=1 и не равны торговой прибыльности.")
    if training is None:
        render_empty_state("Сначала запустите walk-forward", "После проверки здесь появятся ML-метрики модели.")
    else:
        metrics = training["metrics"]
        metric_cols = st.columns(5)
        metric_cols[0].metric("Точность", f"{metrics['accuracy']:.3f}")
        metric_cols[1].metric("Точность сигналов", f"{metrics['precision']:.3f}")
        metric_cols[2].metric("Полнота", f"{metrics['recall']:.3f}")
        metric_cols[3].metric("F1", f"{metrics['f1']:.3f}")
        metric_cols[4].metric("Target=1", f"{training['positive_rate']:.2%}")
        feature_importance = training.get("feature_importance")
        if not demo_mode:
            with st.expander("Feature importance", expanded=False):
                if feature_importance:
                    importance = pd.DataFrame(
                        feature_importance.items(),
                        columns=["Признак", "Важность"],
                    )
                    render_dark_table(importance)
                else:
                    st.info("В walk-forward режиме важность признаков не агрегируется.")

with walk_forward_tab:
    st.markdown('<div class="section-title">Walk-forward проверка</div>', unsafe_allow_html=True)
    st.caption(
        "Walk-forward обучает модель на прошлом отрезке и проверяет ее на следующем будущем окне. "
        "Так видно, насколько стратегия держится вне обучающей выборки."
    )
    if walk_forward is None:
        render_empty_state("Сначала запустите walk-forward", "Здесь появятся fold-метрики и таблица окон.")
    else:
        metrics = walk_forward["metrics"]
        wf_cols = st.columns(6)
        wf_cols[0].metric("Окон", walk_forward["fold_count"])
        wf_cols[1].metric("Test rows", walk_forward["total_test_rows"])
        wf_cols[2].metric("Target=1", f"{walk_forward['positive_rate']:.2%}")
        wf_cols[3].metric("Precision", f"{metrics['precision']:.3f}")
        wf_cols[4].metric("Recall", f"{metrics['recall']:.3f}")
        wf_cols[5].metric("F1", f"{metrics['f1']:.3f}")
        with st.expander("Полная таблица fold/window", expanded=False):
            render_dark_table(localize_walk_forward_folds(walk_forward))

    st.markdown('<div class="section-title">Бэктест по окнам</div>', unsafe_allow_html=True)
    if walk_forward_window_backtests.empty:
        render_empty_state("Сначала запустите walk-forward", "Здесь появится бэктест по каждому тестовому окну.")
    else:
        positive_windows = int((walk_forward_window_backtests["pnl"] > 0).sum())
        window_cols = st.columns(4)
        window_cols[0].metric("Плюсовых окон", f"{positive_windows}/{len(walk_forward_window_backtests)}")
        window_cols[1].metric("Сумма PnL", format_money(walk_forward_window_backtests["pnl"].sum()))
        window_cols[2].metric("Сделок", int(walk_forward_window_backtests["trades"].sum()))
        worst_window = walk_forward_window_backtests["pnl"].min()
        window_cols[3].metric("Худшее окно", format_money(worst_window))
        st.plotly_chart(
            create_walk_forward_windows_figure(walk_forward_window_backtests),
            use_container_width=True,
            key="walk_forward_windows_detail",
        )
        with st.expander("Полная таблица окон", expanded=False):
            render_dark_table(localize_window_backtests(walk_forward_window_backtests))

    if not demo_mode:
        with st.expander("Диагностика сигналов по окнам", expanded=False):
            if walk_forward_signal_diagnostics.empty:
                st.info("Диагностика появится после запуска walk-forward.")
            else:
                render_dark_table(localize_signal_diagnostics(walk_forward_signal_diagnostics))

        with st.expander("Grid-search / подбор параметров", expanded=False):
            if walk_forward_grid.empty:
                st.info("Подбор параметров доступен в Advanced / Research.")
            else:
                best_row = walk_forward_grid.iloc[0]
                best_cols = st.columns(4)
                best_cols[0].metric("Лучший target", f"{best_row['target']:.3f}")
                best_cols[1].metric("Лучший entry", f"{best_row['entry']:.2f}")
                best_cols[2].metric("PnL", format_money(best_row["pnl"]))
                best_cols[3].metric("Сделок", int(best_row["trades"]))
                render_dark_table(localize_walk_forward_grid(walk_forward_grid))

if signals_tab is not None:
    with signals_tab:
        st.markdown('<div class="section-title">Последние сигналы модели</div>', unsafe_allow_html=True)
        if signals.empty:
            st.info("Сначала обучите модель или запустите walk-forward.")
        else:
            signal_table_columns = [
                column
                for column in [
                    "timestamp",
                    "close",
                    "probability",
                    "signal_direction",
                    "side",
                    "confidence",
                    "ema_20_distance",
                    "trend_direction",
                    "market_regime",
                    "reason",
                    "atr",
                ]
                if column in signals.columns
            ]
            render_dark_table(localize_signals(signals[signal_table_columns].tail(20)), empty_text="Сигналов пока нет.")
            with st.expander("Полный список сигналов", expanded=False):
                render_dark_table(
                    localize_signals(signals[signal_table_columns]),
                    empty_text="Сигналов пока нет.",
                )

with trades_tab:
    st.markdown('<div class="section-title">Сделки по результатам бэктеста</div>', unsafe_allow_html=True)
    if backtest is None:
        render_empty_state("Нет сделок для отображения", "Запустите walk-forward или бэктест, чтобы увидеть сделки.")
    else:
        st.plotly_chart(create_equity_figure(backtest), use_container_width=True, key="trades_equity_curve")
        render_dark_table(
            localize_trades(backtest.get("trades", []), compact=True),
            empty_text="Нет сделок для отображения.",
        )
        with st.expander("Полная таблица сделок", expanded=False):
            render_dark_table(localize_trades(backtest.get("trades", [])), empty_text="Нет сделок для отображения.")

with service_tab:
    st.markdown('<div class="section-title">Состояние сервисов</div>', unsafe_allow_html=True)
    service_cols = st.columns(5)
    service_cols[0].metric("Данные", "OK" if not candles.empty else "-")
    service_cols[1].metric("ML", "OK" if training is not None else "-")
    service_cols[2].metric("Сигналы", "OK" if not signals.empty else "-")
    service_cols[3].metric("Бэктест", "OK" if backtest is not None else "-")
    service_cols[4].metric("WF", "OK" if walk_forward is not None else "-")
    if demo_mode:
        st.caption("В demo mode показаны только основные статусы сервисов.")
    else:
        with st.expander("Service debug JSON", expanded=False):
            st.code(
                json.dumps(
                    {
                        "сервис_данных": MARKET_DATA_SERVICE_URL,
                        "ml_сервис": ML_SERVICE_URL,
                        "сервис_стратегии": STRATEGY_SERVICE_URL,
                        "риск_менеджер": RISK_MANAGER_URL,
                        "сервис_бэктеста": BACKTESTING_SERVICE_URL,
                        "данные_загружены": not candles.empty,
                        "модель_обучена": training is not None,
                        "сигналы_сформированы": not signals.empty,
                        "решение_по_риску_готово": risk_decision is not None,
                        "бэктест_готов": backtest is not None,
                        "walk_forward_готов": walk_forward is not None,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
