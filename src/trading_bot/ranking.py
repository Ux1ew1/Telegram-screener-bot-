from __future__ import annotations

from .config import Settings


def normalize(value: float, lower: float, upper: float) -> float:
    if value <= lower:
        return 0.0
    if value >= upper:
        return 100.0
    return ((value - lower) / (upper - lower)) * 100.0


def build_score(
    settings: Settings,
    turnover_24h: float,
    atr_pct: float,
    trend_abs_pct: float,
    corr_abs: float,
) -> float:
    liquidity = normalize(turnover_24h, settings.min_24h_quote_volume, settings.min_24h_quote_volume * 4.0)
    volatility = normalize(atr_pct, 0.5, 6.0)
    trend = normalize(trend_abs_pct, settings.min_abs_trend_pct_4h, 5.0)

    if corr_abs <= settings.correlation_penalty_threshold:
        corr_component = 100.0
    else:
        corr_component = max(
            0.0,
            100.0
            - normalize(
                corr_abs,
                settings.correlation_penalty_threshold,
                1.0,
            ),
        )

    weighted = (
        liquidity * 0.25
        + volatility * 0.30
        + trend * 0.30
        + corr_component * 0.15
    )
    return round(weighted, 2)
