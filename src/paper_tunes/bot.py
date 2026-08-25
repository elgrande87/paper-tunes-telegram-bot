"""Telegram interface for Paper Tunes."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
LOG = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎵 Paper Tunes\n\n"
        "Schick mir später eine Musikdatei, um daraus druckbare QR-Codes zu erzeugen.\n"
        "Schick mir Fotos/Scans von Paper-Tunes-Seiten zurück, um die Musik zu rekonstruieren.\n\n"
        "/status – Bot-Status"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🟢 Paper Tunes Bot läuft.")


async def unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Ich habe die Datei erhalten. Die Audio-En-/Decodierung wird im nächsten Modul integriert."
    )


def build_application(settings: Settings) -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.ATTACHMENT, unsupported))
    app.add_handler(MessageHandler(filters.PHOTO, unsupported))
    return app


def main() -> None:
    settings = Settings()
    LOG.info("Starting Paper Tunes Telegram Bot")
    build_application(settings).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
