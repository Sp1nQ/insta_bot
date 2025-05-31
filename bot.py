import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# Функция скачивания видео
def download_instagram_video(url: str, output_path="video.mp4"):
    ydl_opts = {
        "outtmpl": output_path,
        "quiet": True,
        "cookiefile": "cookies.txt",  # обязательный параметр
        "format": "mp4"
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return output_path

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли ссылку на Instagram-видео — я скачаю его для тебя.")

# Обработка текстовых сообщений (ожидаем ссылку)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "instagram.com" not in url:
        await update.message.reply_text("Пожалуйста, пришли корректную ссылку на видео в Instagram.")
        return

    await update.message.reply_text("Скачиваю видео...")

    try:
        path = download_instagram_video(url)
        await update.message.reply_video(video=open(path, "rb"))
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Произошла ошибка при скачивании. Убедись, что ссылка работает и доступна.")
    finally:
        if os.path.exists("video.mp4"):
            os.remove("video.mp4")

# Запуск бота
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
