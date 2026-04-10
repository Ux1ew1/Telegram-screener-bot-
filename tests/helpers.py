from pathlib import Path

from src.trading_bot.config import Settings


def make_settings() -> Settings:
    return Settings(
        trading_preset="mvp",
        telegram_bot_token="x",
        bybit_api_key="",
        bybit_api_secret="",
        bybit_base_url="https://api.bybit.com",
        scan_interval_min=15,
        min_24h_quote_volume=50_000_000,
        max_symbols_to_analyze=80,
        min_score=45,
        top_n=10,
        atr_period=14,
        sl_atr_mult=1.2,
        rr_ratio=2.0,
        min_abs_trend_pct_4h=0.5,
        correlation_lookback=48,
        correlation_penalty_threshold=0.9,
        dedupe_window_min=180,
        regime_lookback_4h=12,
        min_regime_strength_4h=20,
        confirmation_lookback_15m=10,
        signal_eval_window_min=360,
        data_dir=Path('.'),
        state_file='state.json',
    )
