import os
import asyncio
from aiohttp import web
from telegram.ext import Application, CommandHandler
from handlers import start, save   # your handlers
from google_sheet import setup_sheets  # optional


BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://xxx.onrender.com/webhook


async def telegram_webhook(request):
    bot_app = request.app["bot_app"]
    data = await request.json()
    await bot_app.process_update(data)
    return web.Response(text="OK")


async def main():
    if not BOT_TOKEN:
        raise Exception("BOT_TOKEN is missing in Render env vars")

    # Telegram Application (No Updater!)
    app = Application.builder().token(BOT_TOKEN).build()

    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("save", save))

    # Setup Sheets (optional)
    try:
        setup_sheets()
        print("Google Sheet setup complete.")
    except:
        print("Google Sheet setup skipped.")

    # Set Webhook
    await app.bot.set_webhook(WEBHOOK_URL)

    # Create aiohttp web app
    web_app = web.Application()
    web_app["bot_app"] = app

    # Webhook route
    web_app.router.add_post("/webhook", telegram_webhook)

    # Run web server
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

    print(f"🚀 Bot running on Render with webhook: {WEBHOOK_URL}")

    # Start Telegram application
    await app.start()
    await app.run_polling()  # SAFEST way in PTB >=20 (No Updater class)
    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
