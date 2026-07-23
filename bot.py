import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from app.database.db import init_db
from bot.handlers import main as main_handler
from bot.handlers import admin as admin_handler


async def handle_health(request):
    return web.Response(text="ok")


async def run_web_server():
    # Render (and most free hosts) require a web service to bind to $PORT.
    # This tiny server exists only to satisfy that requirement and to give
    # uptime pingers something to hit — it has nothing to do with bot logic.
    port = int(os.getenv("PORT", "10000"))
    app = web.Application()
    app.router.add_get("/", handle_health)
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
