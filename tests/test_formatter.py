from src.trading_bot.formatter import format_signals, format_top
from src.trading_bot.models import ScanMetric, Signal


def test_format_top_and_signals():
    top = [
        ScanMetric(
            symbol="BTCUSDT",
            score=77.2,
            last_price=50000,
            turnover_24h=1_000_000_000,
            atr_value=500,
            atr_pct=1,
            trend_pct_4h=2,
            correlation_btc=1.0,
            side="LONG",
            signal_ts=1700000000000,
            regime_strength_4h=55,
            reasons=["a"],
        )
    ]
    signals = [
        Signal(
            symbol="BTCUSDT",
            side="LONG",
            entry=50000,
            sl=49500,
            tp=51000,
            rr=2,
            score=77.2,
            timeframes="1h+4h+15m",
            reason="a",
            created_ts=1700000000000,
        )
    ]

    top_text = format_top(top)
    signal_text = format_signals(signals)

    assert "BTCUSDT" in top_text
    assert "Сила тренда" in top_text
    assert "LONG" in signal_text
