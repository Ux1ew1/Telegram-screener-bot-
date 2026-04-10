from __future__ import annotations

from .config import Settings
from .models import ScanMetric, Signal


def build_signal(metric: ScanMetric, settings: Settings) -> Signal | None:
    if metric.atr_value <= 0:
        return None

    entry = metric.last_price
    risk = metric.atr_value * settings.sl_atr_mult
    if risk <= 0:
        return None

    if metric.side == "LONG":
        sl = entry - risk
        if sl <= 0:
            return None
        tp = entry + (entry - sl) * settings.rr_ratio
    else:
        sl = entry + risk
        tp = entry - (sl - entry) * settings.rr_ratio
        if tp <= 0:
            return None

    reason = "; ".join(metric.reasons)

    return Signal(
        symbol=metric.symbol,
        side=metric.side,
        entry=entry,
        sl=sl,
        tp=tp,
        rr=settings.rr_ratio,
        score=metric.score,
        timeframes="1h+4h+15m",
        reason=reason,
        created_ts=metric.signal_ts,
    )
