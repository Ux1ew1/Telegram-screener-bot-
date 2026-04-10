from __future__ import annotations

from .models import ScanMetric, Signal


def _side_label(side: str) -> str:
    if side == "LONG":
        return "ЛОНГ"
    if side == "SHORT":
        return "ШОРТ"
    return side


def _fmt_price(value: float) -> str:
    if value >= 1000:
        return f"{value:,.2f}"
    if value >= 1:
        return f"{value:.4f}"
    return f"{value:.6f}"


def format_top(metrics: list[ScanMetric]) -> str:
    if not metrics:
        return "TOP: подходящих монет не найдено."

    lines = ["Рейтинг монет Bybit USDT Perpetual:"]
    for i, m in enumerate(metrics, start=1):
        lines.append(
            f"{i}. {m.symbol} | Балл={m.score:.1f} | Объем24ч={m.turnover_24h:,.0f} | "
            f"ATR% (1ч)={m.atr_pct:.2f} | Тренд4ч={m.trend_pct_4h:.2f}% | "
            f"Сила тренда={m.regime_strength_4h:.1f} | Корр.BTC={m.correlation_btc:.2f}"
        )
    return "\n".join(lines)


def format_signals(signals: list[Signal]) -> str:
    if not signals:
        return "SIGNAL: сетапов не найдено."

    lines = ["Сигналы:"]
    for s in signals:
        lines.append(
            f"{s.symbol} {_side_label(s.side)} ({s.side}) | Вход={_fmt_price(s.entry)} | SL={_fmt_price(s.sl)} | "
            f"TP={_fmt_price(s.tp)} | R/R={s.rr:.2f} | Балл={s.score:.1f}"
        )
        if s.reason:
            lines.append(f"Причина: {s.reason}")
    return "\n".join(lines)
