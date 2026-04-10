from src.trading_bot.indicators import atr, breakout_confirmation, pearson_corr, returns, trend_efficiency, trend_pct
from src.trading_bot.models import Candle


def test_returns():
    data = [100.0, 105.0, 99.75]
    r = returns(data)
    assert len(r) == 2
    assert round(r[0], 4) == 0.05


def test_atr_positive():
    candles = [
        Candle(ts=i, open=10 + i, high=11 + i, low=9 + i, close=10.5 + i, volume=100)
        for i in range(20)
    ]
    value = atr(candles, 14)
    assert value > 0


def test_trend_pct():
    candles = [
        Candle(ts=1, open=10, high=10, low=10, close=10, volume=1),
        Candle(ts=2, open=12, high=12, low=12, close=12, volume=1),
    ]
    assert trend_pct(candles) == 20.0


def test_trend_efficiency_range():
    candles = [
        Candle(ts=i, open=100 + i, high=101 + i, low=99 + i, close=100 + i, volume=1)
        for i in range(30)
    ]
    val = trend_efficiency(candles, 12)
    assert 0 <= val <= 100


def test_breakout_confirmation_long():
    candles = [
        Candle(ts=i, open=100, high=101, low=99, close=100, volume=1)
        for i in range(15)
    ]
    candles[-1] = Candle(ts=14, open=100, high=103, low=100, close=102, volume=1)
    assert breakout_confirmation(candles, "LONG", 10)


def test_pearson_corr_near_one():
    a = [1, 2, 3, 4, 5]
    b = [2, 4, 6, 8, 10]
    c = pearson_corr(a, b)
    assert c > 0.99
