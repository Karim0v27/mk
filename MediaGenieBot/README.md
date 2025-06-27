# MediaGenieBot

🎶 Telegram-бот для поиска музыки, фильмов и аниме.

## Возможности

- `/music <название>` — скачивает MP3 с YouTube
- `/movie <название>` — ищет фильм через OMDb API
- `/anime <название>` — ищет аниме через Jikan API

## Деплой на Render

1. Залей папку на GitHub
2. Создай **Web Service** на [Render](https://render.com)
3. В настройках:
   - **Start command:** `python MediaGeniebot.py`
   - **Environment variables:**
     - `BOT_TOKEN` — твой токен от BotFather
     - `RENDER_EXTERNAL_URL` — Render подставит автоматически

## Зависимости

```
python-telegram-bot==20.3
aiohttp
requests
yt_dlp
```

## Автор

Создан с ❤️ на Python.
