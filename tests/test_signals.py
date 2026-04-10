from src.trading_bot.models import ScanMetric
from src.trading_bot.signals import build_signal

from .helpers import make_settings


def test_build_signal_long():
    settings = make_settings()
    metric = ScanMetric(
        symbol="BTCUSDT",
        score=70,
        last_price=100.0,
        turnover_24h=10_000_000,
        atr_value=2.0,
        atr_pct=2.0,
        trend_pct_4h=1.5,
        correlation_btc=0.5,
        side="LONG",
        signal_ts=1700000000000,
        regime_strength_4h=45,
        reasons=["x"],
    )
    s = build_signal(metric, settings)
    assert s is not None
    assert s.side == "LONG"
    assert s.tp > s.entry > s.sl
    assert s.created_ts == metric.signal_ts


def test_build_signal_short():
    settings = make_settings()
    settings.sl_atr_mult = 1.0

    metric = ScanMetric(
        symbol="ETHUSDT",
        score=66,
        last_price=100.0,
        turnover_24h=10_000_000,
        atr_value=3.0,
        atr_pct=3.0,
        trend_pct_4h=-2.0,
        correlation_btc=0.7,
        side="SHORT",
        signal_ts=1700000000000,
        regime_strength_4h=52,
        reasons=["x"],
    )
    s = build_signal(metric, settings)
    assert s is not None
    assert s.side == "SHORT"
    assert s.sl > s.entry > s.tp
