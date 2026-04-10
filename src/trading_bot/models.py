from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Candle:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SymbolTicker:
    symbol: str
    last_price: float
    turnover_24h: float
    price_change_24h: float


@dataclass
class ScanMetric:
    symbol: str
    score: float
    last_price: float
    turnover_24h: float
    atr_value: float
    atr_pct: float
    trend_pct_4h: float
    correlation_btc: float
    side: str
    signal_ts: int
    regime_strength_4h: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class Signal:
    symbol: str
    side: str
    entry: float
    sl: float
    tp: float
    rr: float
    score: float
    timeframes: str
    reason: str
    created_ts: int

    def fingerprint(self) -> str:
        return f"{self.symbol}:{self.side}:{round(self.entry, 6)}:{round(self.sl, 6)}:{round(self.tp, 6)}"
