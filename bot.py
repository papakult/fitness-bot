import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
from aiohttp import web
from app.database.db import init_db
from bot.handlers import main as main_handler
from bot.handlers import admin as admin_handler

# Telegram file_ids for the mini-app's media (trainer photo/video, gallery).
# These are NOT secrets by themselves — they're useless without the bot
# token, which stays server-side here and is never sent to the browser.
MEDIA_FILE_IDS = {
    "trainer-photo": "AgACAgIAAxkBAAICZGpG0z4rzjd5DaP2r12FpOneTFCJAAINFGsbVgs5SkNsauhDmCYvAQADAgADeQADPAQ",
    "trainer-video": "BAACAgIAAxkBAAICZmpG02JEuJU5UDFXqGW1Ra6BPJAUAALrlgACVgs5She3467ebX5ZPAQ",
    "gallery-1": "AgACAgIAAxkBAAICeGpG2BwcSF2A0OpQ65NmSD21HmVhAAIcFGsbVgs5SnzBvOz1Jm6GAQADAgADdwADPAQ",
    "gallery-2": "AgACAgIAAxkBAAICdmpG2BJHBq0CRN5swIxIUuThjrS7AAIbFGsbVgs5SsE682BNbzonAQADAgADdwADPAQ",
    "gallery-3": "AgACAgIAAxkBAAICdGpG2A_0s85XO2wvRzzabJ30m8XGAAIaFGsbVgs5SsNwiJ1sBNu3AQADAgADdwADPAQ",
    "gallery-4": "AgACAgIAAxkBAAICcmpG2As4c-wyCuYsLg_QPE_f_zjVAAIZFGsbVgs5Sopc2dW63MqwAQADAgADeQADPAQ",
    "gallery-5": "AgACAgIAAxkBAAICcGpG2AdiPA8OBwIAAZlNNFXuuhChdQACGBRrG1YLOUqVBs7A2XmbNAEAAwIAA3kAAzwE",
    "gallery-6": "AgACAgIAAxkBAAICbmpG2AL_ZBQEU2iIFlyeXkZmdrk5AAIXFGsbVgs5Sg3RretEro67AQADAgADdwADPAQ",
}

# Simple in-memory cache so repeat visits don't re-hit the Telegram API.
_media_cache = {}


async def handle_health(request):
    return web.Response(text="ok")


async def handle_media(request):
    key = request.match_info.get("key")
    file_id = MEDIA_FILE_IDS.get(key)
    if not file_id:
        return web.Response(status=404, text="not found")

    if key in _media_cache:
        content, content_type = _media_cache[key]
        return web.Response(
            body=content,
            content_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )

    bot_token = os.getenv("BOT_TOKEN")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.telegram.org/bot{bot_token}/getFile",
            params={"file_id": file_id},
        ) as resp:
            data = await resp.json()
        if not data.get("ok"):
            return web.Response(status=502, text="telegram error")
        file_path = data["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        async with session.get(file_url) as file_resp:
            content = await file_resp.read()
            content_type = file_resp.headers.get("Content-Type", "application/octet-stream")

    _media_cache[key] = (content, content_type)
    return web.Response(
        body=content,
        content_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


async def run_web_server():
    # Render (and most free hosts) require a web service to bind to $PORT.
    # This server also proxies mini-app media (photo/video/gallery) so the
    # bot token never has to be embedded in client-side JS.
    port = int(os.getenv("PORT", "10000"))
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/media/{key}", handle_media)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Health check server started on port {port}")


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_handler.router)
    dp.include_router(admin_handler.router)
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await run_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
