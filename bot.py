import os
import json
import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)


def get_video_metadata(input_file):
    """Получить метаданные видео (ширина, высота, угол поворота)."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,rotation,sample_aspect_ratio",
        "-of", "json",
        input_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        info = json.loads(result.stdout)
        stream = info["streams"][0]
        width = stream.get("width")
        height = stream.get("height")
        rotation = stream.get("rotation", 0) or stream.get("tags", {}).get("rotate", 0)
        if rotation:
            rotation = int(rotation)
        else:
            rotation = 0
        sar = stream.get("sample_aspect_ratio", "1:1")
    except (KeyError, IndexError, ValueError, json.JSONDecodeError):
        width = height = rotation = 0
        sar = "1:1"
    return width, height, rotation, sar


def correct_rotation_and_scale(input_file, output_file):
    width, height, rotation, sar = get_video_metadata(input_file)

    # Формируем фильтр поворота
    if rotation == 90:
        vf_filters = "transpose=1"
        # поменяем местами ширину и высоту после поворота
        width, height = height, width
    elif rotation == 180:
        vf_filters = "transpose=2,transpose=2"
    elif rotation == 270:
        vf_filters = "transpose=2"
        width, height = height, width
    else:
        vf_filters = None

    # Добавляем масштабирование с сохранением пропорций и выравниванием по 2
    # Здесь мы просто выравниваем по 2, без изменения разрешения
    scale_filter = f"scale=trunc(iw/2)*2:trunc(ih/2)*2"

    if vf_filters:
        full_filter = f"{vf_filters},{scale_filter}"
    else:
        full_filter = scale_filter

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-vf", full_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-movflags", "+faststart",
        "-c:a", "copy",
        output_file
    ]

    subprocess.run(cmd, check=True)


def download_instagram_video(url: str, output_path="video.mp4"):
    temp_path = "raw_instagram_video.mp4"

    ydl_opts = {
        "outtmpl": temp_path,
        "quiet": True,
        "cookiefile": "cookies.txt",  # если используете куки, иначе можно убрать
        "format": "mp4"
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    correct_rotation_and_scale(temp_path, output_path)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    return output_path


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
        await update.message.reply_video(video=open(path, "rb"))
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Произошла ошибка при скачивании. Убедись, что ссылка работает и доступна.")
    finally:
        if os.path.exists("video.mp4"):
            os.remove("video.mp4")


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
