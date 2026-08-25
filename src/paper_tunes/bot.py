from __future__ import annotations

import logging
from collections import defaultdict

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .config import settings
from .qr import QRDecodeError, decode_qr_codes
from .qr_protocol import Chunk, ProtocolError, assemble_chunks, parse_chunk

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
_pending: dict[int, dict[str, dict[int, Chunk]]] = defaultdict(lambda: defaultdict(dict))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Send me a photo or image document containing Paper Tunes QR codes. "
            "You may send pages one after another; I return the reconstructed file when complete."
        )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        _pending.pop(update.effective_chat.id, None)
    if update.message:
        await update.message.reply_text("Stored QR fragments cleared.")


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat = update.effective_chat
    if not message or not chat:
        return

    upload = message.document or (message.photo[-1] if message.photo else None)
    if upload is None:
        return
    if message.document and message.document.mime_type and not message.document.mime_type.startswith("image/"):
        await message.reply_text("Please send an image file.")
        return

    await context.bot.send_chat_action(chat.id, ChatAction.TYPING)
    try:
        telegram_file = await upload.get_file()
        image = bytes(await telegram_file.download_as_bytearray())
        values = decode_qr_codes(image)
        chunks = [parse_chunk(value) for value in values]

        completed: list[tuple[str, bytes]] = []
        for chunk in chunks:
            stored = _pending[chat.id][chunk.file_id]
            previous = stored.get(chunk.index)
            if previous and previous.payload != chunk.payload:
                raise ProtocolError(f"Conflicting chunk {chunk.index}")
            stored[chunk.index] = chunk
            if len(stored) == chunk.total:
                completed.append(assemble_chunks(list(stored.values())))

        if not completed:
            progress = []
            for file_id, stored in _pending[chat.id].items():
                total = next(iter(stored.values())).total
                progress.append(f"{file_id}: {len(stored)}/{total}")
            await message.reply_text("QR fragments saved. " + ", ".join(progress))
            return

        for file_id, data in completed:
            await context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_DOCUMENT)
            await message.reply_document(document=data, filename=f"{file_id}.bin")
            del _pending[chat.id][file_id]
    except (QRDecodeError, ProtocolError) as exc:
        await message.reply_text(f"Could not process the image: {exc}")
    except Exception:
        logger.exception("Unexpected upload processing error")
        await message.reply_text("Processing failed unexpectedly. Please try a sharper original image.")


def main() -> None:
    if not settings.telegram_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    app = Application.builder().token(settings.telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_image))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
