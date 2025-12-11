# main.py

import os
from aiohttp import web
from telegram.ext import (
    Application,
    CommandHandler
)
from handlers import start, save


BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://mybot.onrender.com/webhook


async def handle_webhook(request):
    data = await request.json()
    await request.app["bot_app"].update_queue.put(data)
    return web.Response(text="OK")


async def main():
    if not BOT_TOKEN:
        raise Exception("BOT_TOKEN missing in environment variables")

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("save", save))

    # aiohttp Web App
    web_app = web.Application()
    web_app["bot_app"] = app

    web_app.router.add_post("/webhook", handle_webhook)

    # Set Webhook
    await app.bot.set_webhook(WEBHOOK_URL)

    # Run Telegram & Web Server
    runner = web.AppRunner(web_app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

    print("Bot running on Render…")

    await app.start()
    await app.updater.start_polling()  # needed for update queue
    await app.updater.idle()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
