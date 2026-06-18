import os
import uuid
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

def download_instagram_video(url: str):
    video_id = uuid.uuid4().hex

    temp_path = f"raw_{video_id}.mp4"

    ydl_opts = {
        "outtmpl": temp_path,
        "quiet": True,
        "cookiefile": "cookies.txt",
        "format": "mp4"
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    return temp_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли ссылку на Instagram-видео — я скачаю его для тебя.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "instagram.com" not in url:
        await update.message.reply_text("Пожалуйста, пришли корректную ссылку на видео в Instagram.")
        return

    await update.message.reply_text("Скачиваю видео...")

    try:
        path = download_instagram_video(url)

        with open(path, "rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                width=720,
                height=1280,
                supports_streaming=True
            )
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Произошла ошибка при скачивании. Убедись, что ссылка работает и доступна.")
    finally:
        if "path" in locals() and os.path.exists(path):
            os.remove(path)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
