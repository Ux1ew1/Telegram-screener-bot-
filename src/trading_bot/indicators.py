from __future__ import annotations

import math
from typing import Sequence

from .models import Candle


def closes(candles: Sequence[Candle]) -> list[float]:
    return [c.close for c in candles]


def returns(values: Sequence[float]) -> list[float]:
    if len(values) < 2:
        return []
    result: list[float] = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        if prev == 0:
            result.append(0.0)
        else:
            result.append((values[i] - prev) / prev)
    return result


def atr(candles: Sequence[Candle], period: int) -> float:
    if len(candles) < period + 1:
        return 0.0

    trs: list[float] = []
    for i in range(1, len(candles)):
        curr = candles[i]
        prev_close = candles[i - 1].close
        tr = max(
            curr.high - curr.low,
            abs(curr.high - prev_close),
            abs(curr.low - prev_close),
        )
        trs.append(tr)

    window = trs[-period:]
    if not window:
        return 0.0
    return sum(window) / len(window)


def trend_pct(candles: Sequence[Candle]) -> float:
    if len(candles) < 2:
        return 0.0
    first = candles[0].close
    last = candles[-1].close
    if first == 0:
        return 0.0
    return ((last - first) / first) * 100.0


def trend_efficiency(candles: Sequence[Candle], lookback: int) -> float:
    if len(candles) < lookback + 1:
        return 0.0

    seq = candles[-(lookback + 1) :]
    start = seq[0].close
    end = seq[-1].close
    if start == 0:
        return 0.0

    net = abs(end - start)
    path = 0.0
    for i in range(1, len(seq)):
        path += abs(seq[i].close - seq[i - 1].close)

    if path == 0:
        return 0.0
    return (net / path) * 100.0


def breakout_confirmation(candles: Sequence[Candle], side: str, lookback: int) -> bool:
    if len(candles) < lookback + 2:
        return False

    recent = candles[-(lookback + 1) :]
    current = recent[-1]
    previous = recent[:-1]

    if side == "LONG":
        level = max(c.high for c in previous)
        return current.close > level

    level = min(c.low for c in previous)
    return current.close < level


def pearson_corr(a: Sequence[float], b: Sequence[float]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return 0.0

    a_vals = list(a[-n:])
    b_vals = list(b[-n:])

    mean_a = sum(a_vals) / n
    mean_b = sum(b_vals) / n

    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a_vals, b_vals))
    var_a = sum((x - mean_a) ** 2 for x in a_vals)
    var_b = sum((y - mean_b) ** 2 for y in b_vals)

    if var_a == 0 or var_b == 0:
        return 0.0

    return cov / math.sqrt(var_a * var_b)
