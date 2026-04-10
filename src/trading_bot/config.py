from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


@dataclass
class Settings:
    telegram_bot_token: str
    bybit_api_key: str
    bybit_api_secret: str
    bybit_base_url: str

    scan_interval_min: int
    min_24h_quote_volume: float
    max_symbols_to_analyze: int
    min_score: float
    top_n: int

    atr_period: int
    sl_atr_mult: float
    rr_ratio: float
    min_abs_trend_pct_4h: float

    correlation_lookback: int
    correlation_penalty_threshold: float
    dedupe_window_min: int

    regime_lookback_4h: int
    min_regime_strength_4h: float
    confirmation_lookback_15m: int
    signal_eval_window_min: int

    data_dir: Path
    state_file: str


NUMERIC_FIELDS = {
    "SCAN_INTERVAL_MIN": int,
    "MIN_24H_QUOTE_VOLUME": float,
    "MAX_SYMBOLS_TO_ANALYZE": int,
    "MIN_SCORE": float,
    "TOP_N": int,
    "ATR_PERIOD": int,
    "SL_ATR_MULT": float,
    "RR_RATIO": float,
    "MIN_ABS_TREND_PCT_4H": float,
    "CORRELATION_LOOKBACK": int,
    "CORRELATION_PENALTY_THRESHOLD": float,
    "DEDUPE_WINDOW_MIN": int,
    "REGIME_LOOKBACK_4H": int,
    "MIN_REGIME_STRENGTH_4H": float,
    "CONFIRMATION_LOOKBACK_15M": int,
    "SIGNAL_EVAL_WINDOW_MIN": int,
}


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def load_settings() -> Settings:
    if load_dotenv is not None:
        load_dotenv()

    data_dir = Path(_get_env("DATA_DIR", "./data"))

    return Settings(
        telegram_bot_token=_get_env("TELEGRAM_BOT_TOKEN", ""),
        bybit_api_key=_get_env("BYBIT_API_KEY", ""),
        bybit_api_secret=_get_env("BYBIT_API_SECRET", ""),
        bybit_base_url=_get_env("BYBIT_BASE_URL", "https://api.bybit.com"),
        scan_interval_min=int(_get_env("SCAN_INTERVAL_MIN", "15")),
        min_24h_quote_volume=float(_get_env("MIN_24H_QUOTE_VOLUME", "50000000")),
        max_symbols_to_analyze=int(_get_env("MAX_SYMBOLS_TO_ANALYZE", "80")),
        min_score=float(_get_env("MIN_SCORE", "45")),
        top_n=int(_get_env("TOP_N", "10")),
        atr_period=int(_get_env("ATR_PERIOD", "14")),
        sl_atr_mult=float(_get_env("SL_ATR_MULT", "1.2")),
        rr_ratio=float(_get_env("RR_RATIO", "2.0")),
        min_abs_trend_pct_4h=float(_get_env("MIN_ABS_TREND_PCT_4H", "0.5")),
        correlation_lookback=int(_get_env("CORRELATION_LOOKBACK", "48")),
        correlation_penalty_threshold=float(_get_env("CORRELATION_PENALTY_THRESHOLD", "0.9")),
        dedupe_window_min=int(_get_env("DEDUPE_WINDOW_MIN", "180")),
        regime_lookback_4h=int(_get_env("REGIME_LOOKBACK_4H", "12")),
        min_regime_strength_4h=float(_get_env("MIN_REGIME_STRENGTH_4H", "35")),
        confirmation_lookback_15m=int(_get_env("CONFIRMATION_LOOKBACK_15M", "20")),
        signal_eval_window_min=int(_get_env("SIGNAL_EVAL_WINDOW_MIN", "360")),
        data_dir=data_dir,
        state_file=_get_env("STATE_FILE", "state.json"),
    )


def apply_override(settings: Settings, key: str, raw_value: str) -> None:
    caster = NUMERIC_FIELDS.get(key)
    if caster is None:
        raise KeyError(f"Unsupported setting key: {key}")

    value = caster(raw_value)
    attr = key.lower()
    setattr(settings, attr, value)
