from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

from .models import Candle, SymbolTicker


@dataclass
class BybitClient:
    api_key: str
    api_secret: str
    base_url: str = "https://api.bybit.com"
    timeout_sec: int = 12

    def __post_init__(self) -> None:
        self._session = requests.Session()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}{path}"
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self._session.get(url, params=params, timeout=self.timeout_sec)
                response.raise_for_status()
                payload = response.json()
                if payload.get("retCode") != 0:
                    raise RuntimeError(f"Bybit error: {payload}")
                return payload
            except Exception as exc:  # pragma: no cover
                last_error = exc
                time.sleep(0.6 * (attempt + 1))
        raise RuntimeError(f"Bybit GET failed for {path}: {last_error}")

    def get_usdt_perpetual_symbols(self) -> list[str]:
        payload = self._get(
            "/v5/market/instruments-info",
            {"category": "linear", "limit": 1000},
        )
        items = payload["result"]["list"]
        symbols: list[str] = []
        for item in items:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue
            if item.get("status") != "Trading":
                continue
            if item.get("contractType") != "LinearPerpetual":
                continue
            symbols.append(symbol)
        return symbols

    def get_tickers(self) -> dict[str, SymbolTicker]:
        payload = self._get(
            "/v5/market/tickers",
            {"category": "linear"},
        )
        items = payload["result"]["list"]
        out: dict[str, SymbolTicker] = {}
        for item in items:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue
            out[symbol] = SymbolTicker(
                symbol=symbol,
                last_price=float(item.get("lastPrice", 0) or 0),
                turnover_24h=float(item.get("turnover24h", 0) or 0),
                price_change_24h=float(item.get("price24hPcnt", 0) or 0) * 100.0,
            )
        return out

    def get_kline(self, symbol: str, interval: str, limit: int) -> list[Candle]:
        payload = self._get(
            "/v5/market/kline",
            {
                "category": "linear",
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
        )
        rows = payload["result"]["list"]
        rows = list(reversed(rows))
        candles: list[Candle] = []
        for row in rows:
            candles.append(
                Candle(
                    ts=int(row[0]),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
        return candles
