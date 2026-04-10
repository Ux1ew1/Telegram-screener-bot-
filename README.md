# trading-telegram-bot

Telegram-бот для отбора монет Bybit USDT Perpetual (MVP):
- 📈 сканирует рынок каждые N минут;
- 🧠 считает скоринг монет по ликвидности, волатильности, тренду и корреляции с BTC;
- 📩 отправляет `TOP` и готовые `SIGNAL` сообщения в Telegram.

## 🚀 Возможности MVP
- Только сигналы, без автоторговли.
- Таймфреймы анализа: `1h + 4h` + подтверждение `15m`.
- Фильтр режима рынка (сила тренда на 4ч) для отсева флэта.
- Направления: `Long + Short`.
- Риск-модель: `ATR-based SL/TP` с фиксированным `R:R`.
- Команды: `/start`, `/scan`, `/top`, `/settings`, `/stats`.
- Авто-рассылка по подписанным чатам.
- Журнал сигналов с оценкой результата через заданное окно времени.

## ⚡ Быстрый старт
1. Установите Python 3.11+.
2. Создайте и активируйте виртуальное окружение:
   - Windows (PowerShell):
     - `python -m venv .venv`
     - `.venv\Scripts\Activate.ps1`
   - Linux/macOS:
     - `python3 -m venv .venv`
     - `source .venv/bin/activate`
3. Установите зависимости:
   - `pip install -r requirements.txt`
4. Скопируйте `.env.example` в `.env` и заполните ключи.
   - Для интрадей-режима установите `TRADING_PRESET=intraday`.
5. Запуск:
   - `python -m src.trading_bot.main`

## 📱 Android (Termux)
1. `pkg update && pkg install python git`
2. Клонируйте проект и перейдите в папку проекта.
3. Создайте и активируйте виртуальное окружение:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
4. Установите зависимости:
   - `pip install -r requirements.txt`
5. Создайте `.env`.
6. Запустите `python -m src.trading_bot.main`.

## ⚙️ Команды
- `/scan` — принудительный скан рынка и вывод сетапов.
- `/top` — только рейтинг монет.
- `/settings` — показать или изменить параметры (`/settings KEY VALUE`).
- `/stats` — статистика отработки сигналов (winrate, avg R, открытые/закрытые).

Поддерживаемые ключи:
- `SCAN_INTERVAL_MIN`
- `MIN_24H_QUOTE_VOLUME`
- `MAX_SYMBOLS_TO_ANALYZE`
- `MIN_SCORE`
- `TOP_N`
- `ATR_PERIOD`
- `SL_ATR_MULT`
- `RR_RATIO`
- `MIN_ABS_TREND_PCT_4H`
- `CORRELATION_LOOKBACK`
- `CORRELATION_PENALTY_THRESHOLD`
- `DEDUPE_WINDOW_MIN`
- `REGIME_LOOKBACK_4H`
- `MIN_REGIME_STRENGTH_4H`
- `CONFIRMATION_LOOKBACK_15M`
- `SIGNAL_EVAL_WINDOW_MIN`

Расшифровка ключей:
- `TRADING_PRESET` — базовый пресет настроек. Доступно: `mvp` (по умолчанию), `intraday`.
- `SCAN_INTERVAL_MIN` — интервал автоскана в минутах.
- `MIN_24H_QUOTE_VOLUME` — минимальный объем торгов за 24ч для монеты (в USDT).
- `MAX_SYMBOLS_TO_ANALYZE` — сколько самых ликвидных монет анализировать за цикл.
- `MIN_SCORE` — минимальный скор, при котором монета попадает в результаты.
- `TOP_N` — сколько монет выводить в рейтинге.
- `ATR_PERIOD` — период ATR для расчета волатильности.
- `SL_ATR_MULT` — множитель ATR для постановки стоп-лосса.
- `RR_RATIO` — соотношение риск/прибыль (например, `2.0` = 1:2).
- `MIN_ABS_TREND_PCT_4H` — минимальная абсолютная величина тренда на 4ч в процентах.
- `CORRELATION_LOOKBACK` — размер окна (в свечах 1ч) для расчета корреляции с BTC.
- `CORRELATION_PENALTY_THRESHOLD` — порог корреляции, после которого скор начинает штрафоваться.
- `DEDUPE_WINDOW_MIN` — окно антидублирования одинаковых сигналов в минутах.
- `REGIME_LOOKBACK_4H` — окно (в свечах 4ч) для оценки силы тренда.
- `MIN_REGIME_STRENGTH_4H` — минимальная сила тренда (0-100), ниже которой сигнал отбрасывается как флэт.
- `CONFIRMATION_LOOKBACK_15M` — сколько свечей `15m` брать для подтверждения пробоя.
- `SIGNAL_EVAL_WINDOW_MIN` — через сколько минут закрывать сигнал в статистике и считать результат.

Параметры пресета `intraday` (если соответствующий ключ не задан вручную в `.env`):
- `SCAN_INTERVAL_MIN=5`
- `MIN_24H_QUOTE_VOLUME=80000000`
- `MAX_SYMBOLS_TO_ANALYZE=120`
- `MIN_SCORE=50`
- `TOP_N=12`
- `SL_ATR_MULT=1.1`
- `RR_RATIO=1.8`
- `MIN_ABS_TREND_PCT_4H=0.35`
- `CORRELATION_LOOKBACK=36`
- `CORRELATION_PENALTY_THRESHOLD=0.85`
- `DEDUPE_WINDOW_MIN=90`
- `REGIME_LOOKBACK_4H=10`
- `MIN_REGIME_STRENGTH_4H=30`
- `CONFIRMATION_LOOKBACK_15M=16`
- `SIGNAL_EVAL_WINDOW_MIN=180`

## ❗ Важно
Сигналы являются аналитическими и не являются финансовой рекомендацией.

## 🛠️ Если видите ошибку про JobQueue
- Обновите зависимости в активном venv:
  - `pip install -r requirements.txt`
- Если нужно вручную:
  - `pip install "python-telegram-bot[job-queue]==21.6"`
