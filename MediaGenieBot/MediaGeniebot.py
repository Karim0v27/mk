import logging
import os
import requests
import aiohttp
import yt_dlp

from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# 🔐 Токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = "73603e14"

# Логирование
logging.basicConfig(level=logging.INFO)

# ==== Переводчик ====
def translate_to_en(text):
    try:
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text},
            timeout=5
        )
        result = response.json()
        return result[0][0][0]
    except Exception as e:
        print("❌ Ошибка перевода:", e)
        return text

# ==== MUSIC ====
def download_audio(query):
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)['entries'][0]
            title = info['title']
            file_path = os.path.join(output_dir, f"{title}.mp3")
            return file_path if os.path.exists(file_path) else None
        except Exception as e:
            print("❌ Ошибка загрузки музыки:", e)
            return None

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🎵 Введите название песни:\n/music название")
        return
    await update.message.reply_text("⌛ Ищу и загружаю песню...")
    file_path = download_audio(query)
    if file_path:
        try:
            with open(file_path, "rb") as audio:
                await update.message.reply_audio(audio=audio)
        finally:
            os.remove(file_path)
    else:
        await update.message.reply_text("❌ Не удалось загрузить песню.")

# ==== MOVIE ====
def get_movie_info(title):
    title_en = translate_to_en(title)
    url = "http://www.omdbapi.com/"
    params = {
        "t": title_en,
        "apikey": OMDB_API_KEY,
        "plot": "short"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("Response") == "True":
            imdb_url = f"https://www.imdb.com/title/{data.get('imdbID')}"
            search_slug = data["Title"].lower().replace(" ", "-")
            kinogo_url = f"https://kinogo.biz/index.php?do=search&subaction=search&story={data['Title']}"
            jut_su_url = f"https://jut.su/{search_slug}/"

            info = f"🎬 *{data['Title']}* ({data['Year']})\n"                    f"⭐ IMDb: {data.get('imdbRating', 'N/A')}\n"                    f"📖 {data.get('Plot', 'Нет описания.')}\n\n"                    f"[IMDb]({imdb_url}) | [Kinogo]({kinogo_url}) | [Jut.su]({jut_su_url})"

            poster = data.get("Poster", None)
            return info, poster
    except Exception as e:
        print("OMDb ошибка:", e)
    return None, None

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🎬 Введите название фильма:\n/movie название")
        return
    await update.message.reply_text("🔍 Ищу информацию...")
    info, poster = get_movie_info(query)
    if info:
        if poster and poster != "N/A":
            await update.message.reply_photo(photo=poster, caption=info, parse_mode="Markdown")
        else:
            await update.message.reply_text(info, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Фильм не найден.")

# ==== ANIME ====
async def get_anime_info(title):
    title_en = translate_to_en(title)
    url = f"https://api.jikan.moe/v4/anime?q={title_en}&limit=1"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if data.get("data"):
                    anime = data["data"][0]
                    name = anime["title"]
                    score = anime.get("score", "N/A")
                    synopsis = anime.get("synopsis", "Нет описания.")
                    image = anime["images"]["jpg"]["image_url"]
                    mal_url = anime["url"]
                    slug = name.lower().replace(" ", "-")
                    kinogo_url = f"https://kinogo.biz/index.php?do=search&subaction=search&story={name}"
                    jut_su_url = f"https://jut.su/{slug}/"

                    text = f"🎌 *{name}*\n"                            f"⭐ Score: {score}\n"                            f"📖 {synopsis}\n\n"                            f"[MyAnimeList]({mal_url}) | [Kinogo]({kinogo_url}) | [Jut.su]({jut_su_url})"

                    return text, image
    except Exception as e:
        print("Jikan API ошибка:", e)
    return None, None

async def anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🎌 Введите название аниме:\n/anime Naruto")
        return
    await update.message.reply_text("🔍 Ищу информацию...")
    info, image = await get_anime_info(query)
    if info:
        if image:
            if len(info) <= 1024:
                await update.message.reply_photo(photo=image, caption=info, parse_mode="Markdown")
            else:
                await update.message.reply_photo(photo=image)
                await update.message.reply_text(info, parse_mode="Markdown")
        else:
            await update.message.reply_text(info, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Аниме не найдено.")

# ==== START ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎵 Музыка"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Привет! Я мультимедийный бот 🎶🎬🎌\n\n"
        "Команды:\n"
        "/music <название> — найти песню\n"
        "/movie <название> — найти фильм\n"
        "/anime <название> — найти аниме\n",
        reply_markup=reply_markup
    )

async def handle_music_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Введите название песни через /music")

# ==== WEBHOOK HANDLER ====
async def telegram_webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, context.bot)
    await app.update_queue.put(update)
    return web.Response()

async def on_startup(app_aiohttp):
    webhook_url = os.environ["RENDER_EXTERNAL_URL"] + "/webhook"
    await app.bot.set_webhook(webhook_url)
    print("🚀 Webhook установлен:", webhook_url)

# ==== MAIN ====
def main():
    global app, context
    app = ApplicationBuilder().token(TOKEN).build()
    context = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(CommandHandler("movie", movie))
    app.add_handler(CommandHandler("anime", anime))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🎵 Музыка"), handle_music_button))

    aio_app = web.Application()
    aio_app.router.add_post("/webhook", telegram_webhook_handler)
    aio_app.on_startup.append(on_startup)

    port = int(os.environ.get("PORT", 8080))
    web.run_app(aio_app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
