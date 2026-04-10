from src.trading_bot.models import Candle, SymbolTicker
from src.trading_bot.scanner import MarketScanner

from .helpers import make_settings


class FakeBybitClient:
    def get_usdt_perpetual_symbols(self):
        return ["BTCUSDT", "ETHUSDT"]

    def get_tickers(self):
        return {
            "BTCUSDT": SymbolTicker("BTCUSDT", 100.0, 1_000_000_000, 2.0),
            "ETHUSDT": SymbolTicker("ETHUSDT", 110.0, 600_000_000, 1.0),
        }

    def get_kline(self, symbol: str, interval: str, limit: int):
        base = 100 if symbol == "BTCUSDT" else 70

        if interval == "15":
            candles = [
                Candle(ts=i * 900000, open=base + i * 0.4, high=base + i * 0.5, low=base + i * 0.3, close=base + i * 0.45, volume=1000)
                for i in range(limit)
            ]
            last = candles[-1]
            candles[-1] = Candle(
                ts=last.ts,
                open=last.open,
                high=last.high + 6.0,
                low=last.low,
                close=last.close + 6.0,
                volume=last.volume,
            )
            return candles

        slope = 1.0 if symbol == "BTCUSDT" else 0.8
        step = 3600000 if interval == "60" else 4 * 3600000
        return [
            Candle(
                ts=i * step,
                open=base + i * slope,
                high=base + i * slope + 1,
                low=base + i * slope - 1,
                close=base + i * slope + 0.3,
                volume=1000,
            )
            for i in range(limit)
        ]


def test_scanner_pipeline():
    settings = make_settings()
    settings.min_24h_quote_volume = 1_000_000
    settings.max_symbols_to_analyze = 20
    settings.min_score = 0
    settings.top_n = 10
    settings.min_abs_trend_pct_4h = 0.1
    settings.correlation_lookback = 20
    settings.correlation_penalty_threshold = 0.99

    scanner = MarketScanner(FakeBybitClient(), settings)
    top, signals = scanner.scan()

    assert len(top) > 0
    assert len(signals) > 0
    assert all(s.symbol for s in signals)
