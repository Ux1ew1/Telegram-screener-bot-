from __future__ import annotations

from .bybit_client import BybitClient
from .config import Settings
from .indicators import atr, breakout_confirmation, closes, pearson_corr, returns, trend_efficiency, trend_pct
from .models import ScanMetric, SymbolTicker
from .ranking import build_score
from .signals import build_signal


class MarketScanner:
    def __init__(self, client: BybitClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    def _reasons(
        self,
        ticker: SymbolTicker,
        atr_pct_val: float,
        trend4h: float,
        regime_strength: float,
        corr: float,
    ) -> list[str]:
        return [
            f"объем24ч={ticker.turnover_24h:,.0f}",
            f"волатильность ATR(1ч)={atr_pct_val:.2f}%",
            f"тренд(4ч)={trend4h:.2f}%",
            f"сила тренда(4ч)={regime_strength:.1f}",
            f"корреляция с BTC={corr:.2f}",
            f"подтверждение входа: пробой на 15м",
        ]

    def scan(self) -> tuple[list[ScanMetric], list]:
        symbols = set(self.client.get_usdt_perpetual_symbols())
        tickers = self.client.get_tickers()

        liquid_tickers = [
            t
            for s, t in tickers.items()
            if s in symbols and t.turnover_24h >= self.settings.min_24h_quote_volume
        ]
        liquid_tickers.sort(key=lambda x: x.turnover_24h, reverse=True)
        universe = liquid_tickers[: self.settings.max_symbols_to_analyze]

        btc_1h = self.client.get_kline("BTCUSDT", "60", self.settings.correlation_lookback + 10)
        btc_returns = returns(closes(btc_1h))

        metrics: list[ScanMetric] = []
        for ticker in universe:
            candles_1h = self.client.get_kline(ticker.symbol, "60", max(80, self.settings.correlation_lookback + 10))
            candles_4h = self.client.get_kline(ticker.symbol, "240", max(60, self.settings.regime_lookback_4h + 10))
            candles_15m = self.client.get_kline(ticker.symbol, "15", max(60, self.settings.confirmation_lookback_15m + 10))

            if len(candles_1h) < self.settings.atr_period + 2 or len(candles_4h) < self.settings.regime_lookback_4h + 2:
                continue

            atr_value = atr(candles_1h, self.settings.atr_period)
            if atr_value <= 0 or ticker.last_price <= 0:
                continue

            atr_pct_val = (atr_value / ticker.last_price) * 100.0
            trend4h = trend_pct(candles_4h)
            if abs(trend4h) < self.settings.min_abs_trend_pct_4h:
                continue

            regime_strength = trend_efficiency(candles_4h, self.settings.regime_lookback_4h)
            if regime_strength < self.settings.min_regime_strength_4h:
                continue

            side = "LONG" if trend4h > 0 else "SHORT"
            if not breakout_confirmation(candles_15m, side, self.settings.confirmation_lookback_15m):
                continue

            symbol_returns = returns(closes(candles_1h))
            corr = pearson_corr(symbol_returns[-self.settings.correlation_lookback :], btc_returns[-self.settings.correlation_lookback :])

            score = build_score(
                self.settings,
                ticker.turnover_24h,
                atr_pct_val,
                abs(trend4h),
                abs(corr),
            )
            if score < self.settings.min_score:
                continue

            metrics.append(
                ScanMetric(
                    symbol=ticker.symbol,
                    score=score,
                    last_price=ticker.last_price,
                    turnover_24h=ticker.turnover_24h,
                    atr_value=atr_value,
                    atr_pct=atr_pct_val,
                    trend_pct_4h=trend4h,
                    correlation_btc=corr,
                    side=side,
                    signal_ts=candles_15m[-1].ts,
                    regime_strength_4h=regime_strength,
                    reasons=self._reasons(ticker, atr_pct_val, trend4h, regime_strength, corr),
                )
            )

        metrics.sort(key=lambda x: x.score, reverse=True)
        top = metrics[: self.settings.top_n]

        signals = []
        for metric in top:
            signal = build_signal(metric, self.settings)
            if signal is not None:
                signals.append(signal)

        return top, signals
