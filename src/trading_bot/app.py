from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from .bybit_client import BybitClient
from .config import NUMERIC_FIELDS, Settings, apply_override
from .formatter import format_signals, format_top
from .scanner import MarketScanner
from .storage import StateStorage

logger = logging.getLogger(__name__)

SETTING_LABELS = {
    "SCAN_INTERVAL_MIN": "Интервал автоскана (минуты)",
    "MIN_24H_QUOTE_VOLUME": "Мин. объем 24ч (USDT)",
    "MAX_SYMBOLS_TO_ANALYZE": "Макс. число монет для анализа",
    "MIN_SCORE": "Мин. балл для отбора",
    "TOP_N": "Сколько монет показывать в ТОПе",
    "ATR_PERIOD": "Период ATR",
    "SL_ATR_MULT": "Множитель ATR для SL",
    "RR_RATIO": "Соотношение риск/прибыль (R/R)",
    "MIN_ABS_TREND_PCT_4H": "Мин. абсолютный тренд 4ч (%)",
    "CORRELATION_LOOKBACK": "Окно корреляции (кол-во свечей 1ч)",
    "CORRELATION_PENALTY_THRESHOLD": "Порог штрафа за корреляцию с BTC",
    "DEDUPE_WINDOW_MIN": "Окно антидубля сигналов (минуты)",
    "REGIME_LOOKBACK_4H": "Окно оценки силы тренда 4ч",
    "MIN_REGIME_STRENGTH_4H": "Мин. сила тренда 4ч (0-100)",
    "CONFIRMATION_LOOKBACK_15M": "Окно подтверждения пробоя 15м",
    "SIGNAL_EVAL_WINDOW_MIN": "Окно оценки сигнала (минуты)",
}


class TradingBotApp:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage = StateStorage(settings.data_dir, settings.state_file)
        self.client = BybitClient(
            api_key=settings.bybit_api_key,
            api_secret=settings.bybit_api_secret,
            base_url=settings.bybit_base_url,
        )
        self.scanner = MarketScanner(self.client, settings)
        self.application: Application | None = None

    def apply_saved_overrides(self) -> None:
        for key, value in self.storage.get_overrides().items():
            try:
                apply_override(self.settings, key, value)
            except Exception:
                logger.warning("Ignoring invalid stored override %s=%s", key, value)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat is None or update.message is None:
            return
        chat_id = update.effective_chat.id
        self.storage.register_chat(chat_id)
        await update.message.reply_text(
            "Бот активирован. Доступные команды: /scan /top /settings /stats\n"
            "Сигналы аналитические, без автоторговли."
        )

    async def _run_scan(self) -> tuple[str, str, list]:
        top, signals = await asyncio.to_thread(self.scanner.scan)
        await asyncio.to_thread(
            self.storage.add_pending_signals,
            signals,
            self.settings.dedupe_window_min,
        )
        await asyncio.to_thread(
            self.storage.resolve_pending_signals,
            self.client,
            self.settings.signal_eval_window_min,
        )
        return format_top(top), format_signals(signals), signals

    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return
        await update.message.reply_text("Запускаю скан...")
        try:
            top_text, signal_text, _ = await self._run_scan()
            await update.message.reply_text(top_text)
            await update.message.reply_text(signal_text)
        except Exception as exc:
            logger.exception("scan command failed")
            await update.message.reply_text(f"Ошибка сканирования: {exc}")

    async def cmd_top(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return
        try:
            top_text, _, _ = await self._run_scan()
            await update.message.reply_text(top_text)
        except Exception as exc:
            logger.exception("top command failed")
            await update.message.reply_text(f"Ошибка: {exc}")

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return

        stats = await asyncio.to_thread(self.storage.get_stats)
        text = (
            "Статистика сигналов:\n"
            f"Закрыто: {int(stats['closed_total'])}\n"
            f"Побед: {int(stats['wins'])} | Поражений: {int(stats['losses'])} | Нет данных: {int(stats['no_data'])}\n"
            f"Winrate: {stats['winrate']:.1f}%\n"
            f"Средний результат (R): {stats['avg_r']:.3f}\n"
            f"Открытых в журнале: {int(stats['pending'])}"
        )
        await update.message.reply_text(text)

    def _settings_dump(self) -> str:
        data = asdict(self.settings)
        lines = ["Текущие настройки бота:"]
        lines.append(f"Активный пресет: {self.settings.trading_preset} (TRADING_PRESET)")
        for key in sorted(NUMERIC_FIELDS.keys()):
            label = SETTING_LABELS.get(key, "Параметр")
            lines.append(f"{label}: {data[key.lower()]} ({key})")
        lines.append("Изменить параметр: /settings KEY VALUE")
        lines.append("Пример: /settings MIN_SCORE 55")
        return "\n".join(lines)

    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return

        args = context.args
        if not args:
            await update.message.reply_text(self._settings_dump())
            return

        if len(args) != 2:
            await update.message.reply_text("Использование: /settings KEY VALUE\nПример: /settings MIN_SCORE 55")
            return

        key = args[0].upper().strip()
        value = args[1].strip()

        if key not in NUMERIC_FIELDS:
            await update.message.reply_text(
                f"Неизвестный ключ: {key}\n"
                f"Покажи список командой /settings"
            )
            return

        try:
            apply_override(self.settings, key, value)
            self.storage.set_override(key, value)
            if key == "SCAN_INTERVAL_MIN":
                self._schedule_job()
            label = SETTING_LABELS.get(key, "Параметр")
            await update.message.reply_text(f"Обновлено: {label} = {value} ({key})")
        except Exception as exc:
            await update.message.reply_text(
                f"Некорректное значение: {exc}\n"
                "Проверь формат числа и повтори команду."
            )

    def _schedule_job(self) -> None:
        if self.application is None:
            return
        if self.application.job_queue is None:
            logger.warning(
                "JobQueue is not available. Scheduled scan is disabled. "
                "Install optional dependency: python-telegram-bot[job-queue]."
            )
            return

        current_jobs = self.application.job_queue.get_jobs_by_name("scheduled_scan")
        for job in current_jobs:
            job.schedule_removal()

        self.application.job_queue.run_repeating(
            callback=self.scheduled_scan,
            interval=self.settings.scan_interval_min * 60,
            first=10,
            name="scheduled_scan",
        )

    async def scheduled_scan(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chats = self.storage.list_chats()
        if not chats:
            return

        try:
            top_text, _, signals = await self._run_scan()
            self.storage.cleanup_sent(max_age_min=max(self.settings.dedupe_window_min * 2, 360))

            for chat_id in chats:
                await context.bot.send_message(chat_id=chat_id, text=top_text)

                fresh_lines = []
                for signal in signals:
                    key = signal.fingerprint()
                    if self.storage.was_recently_sent(chat_id, key, self.settings.dedupe_window_min):
                        continue
                    self.storage.mark_sent(chat_id, key)
                    fresh_lines.append(signal)

                if fresh_lines:
                    from .formatter import format_signals  # local import to keep module clean

                    await context.bot.send_message(chat_id=chat_id, text=format_signals(fresh_lines))
                else:
                    await context.bot.send_message(chat_id=chat_id, text="Новых сигналов за период нет.")

        except Exception as exc:  # pragma: no cover
            logger.exception("scheduled scan failed")
            for chat_id in chats:
                await context.bot.send_message(chat_id=chat_id, text=f"Ошибка фонового скана: {exc}")

    def build(self) -> Application:
        self.apply_saved_overrides()

        app = ApplicationBuilder().token(self.settings.telegram_bot_token).build()
        self.application = app

        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("scan", self.cmd_scan))
        app.add_handler(CommandHandler("top", self.cmd_top))
        app.add_handler(CommandHandler("settings", self.cmd_settings))
        app.add_handler(CommandHandler("stats", self.cmd_stats))

        self._schedule_job()

        return app
