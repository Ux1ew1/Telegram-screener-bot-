from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from .bybit_client import BybitClient
from .models import Signal


class StateStorage:
    def __init__(self, data_dir: Path, file_name: str) -> None:
        self._lock = threading.Lock()
        self._path = data_dir / file_name
        data_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write(
                {
                    "chats": [],
                    "overrides": {},
                    "sent": {},
                    "journal": {
                        "pending": [],
                        "closed": [],
                    },
                }
            )

    def _read(self) -> dict[str, Any]:
        with self._path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, payload: dict[str, Any]) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def register_chat(self, chat_id: int) -> None:
        with self._lock:
            payload = self._read()
            chats = set(payload.get("chats", []))
            chats.add(chat_id)
            payload["chats"] = sorted(chats)
            self._write(payload)

    def list_chats(self) -> list[int]:
        with self._lock:
            payload = self._read()
            return [int(x) for x in payload.get("chats", [])]

    def get_overrides(self) -> dict[str, str]:
        with self._lock:
            payload = self._read()
            raw = payload.get("overrides", {})
            return {str(k): str(v) for k, v in raw.items()}

    def set_override(self, key: str, value: str) -> None:
        with self._lock:
            payload = self._read()
            overrides = payload.get("overrides", {})
            overrides[key] = value
            payload["overrides"] = overrides
            self._write(payload)

    def was_recently_sent(self, chat_id: int, signal_key: str, dedupe_window_min: int) -> bool:
        with self._lock:
            payload = self._read()
            sent = payload.get("sent", {})
            chat_map = sent.get(str(chat_id), {})
            ts = chat_map.get(signal_key)
            if ts is None:
                return False
            age_sec = time.time() - float(ts)
            return age_sec <= dedupe_window_min * 60

    def mark_sent(self, chat_id: int, signal_key: str) -> None:
        with self._lock:
            payload = self._read()
            sent = payload.get("sent", {})
            chat_map = sent.get(str(chat_id), {})
            chat_map[signal_key] = time.time()
            sent[str(chat_id)] = chat_map
            payload["sent"] = sent
            self._write(payload)

    def cleanup_sent(self, max_age_min: int) -> None:
        with self._lock:
            payload = self._read()
            sent = payload.get("sent", {})
            now = time.time()
            ttl_sec = max_age_min * 60

            for chat_id, signals in list(sent.items()):
                filtered = {
                    key: ts
                    for key, ts in signals.items()
                    if now - float(ts) <= ttl_sec
                }
                sent[chat_id] = filtered

            payload["sent"] = sent
            self._write(payload)

    def add_pending_signals(self, signals: list[Signal], dedupe_window_min: int) -> int:
        with self._lock:
            payload = self._read()
            journal = payload.setdefault("journal", {"pending": [], "closed": []})
            pending = journal.setdefault("pending", [])
            now_ts = time.time()
            added = 0

            for signal in signals:
                if self._has_recent_pending(pending, signal, dedupe_window_min, now_ts):
                    continue
                pending.append(
                    {
                        "symbol": signal.symbol,
                        "side": signal.side,
                        "entry": signal.entry,
                        "sl": signal.sl,
                        "tp": signal.tp,
                        "score": signal.score,
                        "reason": signal.reason,
                        "timeframes": signal.timeframes,
                        "created_ts": signal.created_ts,
                        "inserted_ts": now_ts,
                    }
                )
                added += 1

            journal["pending"] = pending
            payload["journal"] = journal
            self._write(payload)
            return added

    def _has_recent_pending(
        self,
        pending: list[dict[str, Any]],
        signal: Signal,
        dedupe_window_min: int,
        now_ts: float,
    ) -> bool:
        for item in pending:
            if item.get("symbol") != signal.symbol or item.get("side") != signal.side:
                continue
            inserted_ts = float(item.get("inserted_ts", 0))
            if now_ts - inserted_ts > dedupe_window_min * 60:
                continue
            entry = float(item.get("entry", 0.0))
            if entry == 0:
                continue
            drift = abs(signal.entry - entry) / entry
            if drift <= 0.003:
                return True
        return False

    def resolve_pending_signals(self, client: BybitClient, eval_window_min: int) -> int:
        with self._lock:
            payload = self._read()
            journal = payload.setdefault("journal", {"pending": [], "closed": []})
            pending = journal.setdefault("pending", [])
            closed = journal.setdefault("closed", [])

            now_ms = int(time.time() * 1000)
            resolved_count = 0
            still_open: list[dict[str, Any]] = []

            for item in pending:
                created_ts = int(item.get("created_ts", 0))
                if created_ts <= 0:
                    still_open.append(item)
                    continue
                age_min = (now_ms - created_ts) / 60000.0
                if age_min < eval_window_min:
                    still_open.append(item)
                    continue

                outcome, pnl_r = self._resolve_outcome(item, client, eval_window_min)
                item["resolved_ts"] = now_ms
                item["outcome"] = outcome
                item["pnl_r"] = pnl_r
                closed.append(item)
                resolved_count += 1

            journal["pending"] = still_open
            journal["closed"] = closed[-1000:]
            payload["journal"] = journal
            self._write(payload)
            return resolved_count

    def _resolve_outcome(self, item: dict[str, Any], client: BybitClient, eval_window_min: int) -> tuple[str, float]:
        symbol = str(item["symbol"])
        side = str(item["side"])
        entry = float(item["entry"])
        sl = float(item["sl"])
        tp = float(item["tp"])
        created_ts = int(item["created_ts"])

        limit = max(50, int(eval_window_min / 15) + 20)
        candles = client.get_kline(symbol, "15", limit)
        relevant = [c for c in candles if c.ts >= created_ts]
        if not relevant:
            return "NO_DATA", 0.0

        for candle in relevant:
            if side == "LONG":
                sl_hit = candle.low <= sl
                tp_hit = candle.high >= tp
                if sl_hit and tp_hit:
                    return "LOSS", -1.0
                if sl_hit:
                    return "LOSS", -1.0
                if tp_hit:
                    return "WIN", 1.0 * ((tp - entry) / max(entry - sl, 1e-9))
            else:
                sl_hit = candle.high >= sl
                tp_hit = candle.low <= tp
                if sl_hit and tp_hit:
                    return "LOSS", -1.0
                if sl_hit:
                    return "LOSS", -1.0
                if tp_hit:
                    return "WIN", 1.0 * ((entry - tp) / max(sl - entry, 1e-9))

        last = relevant[-1].close
        if side == "LONG":
            pnl_r = (last - entry) / max(entry - sl, 1e-9)
        else:
            pnl_r = (entry - last) / max(sl - entry, 1e-9)
        return ("WIN" if pnl_r >= 0 else "LOSS"), pnl_r

    def get_stats(self) -> dict[str, float]:
        with self._lock:
            payload = self._read()
            journal = payload.get("journal", {})
            closed = journal.get("closed", [])
            pending = journal.get("pending", [])

            total = len(closed)
            wins = sum(1 for x in closed if x.get("outcome") == "WIN")
            losses = sum(1 for x in closed if x.get("outcome") == "LOSS")
            no_data = sum(1 for x in closed if x.get("outcome") == "NO_DATA")
            avg_r = 0.0
            if total > 0:
                avg_r = sum(float(x.get("pnl_r", 0.0)) for x in closed) / total

            winrate = (wins / max(wins + losses, 1)) * 100.0
            return {
                "closed_total": float(total),
                "wins": float(wins),
                "losses": float(losses),
                "no_data": float(no_data),
                "pending": float(len(pending)),
                "winrate": winrate,
                "avg_r": avg_r,
            }
