# handlers.py

from telegram import Update
from telegram.ext import ContextTypes
from google_sheet import write_to_sheet


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello 👋 I'm alive and working on Render!")
    

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/save ", "")

    if not text:
        await update.message.reply_text("Usage: /save something")
        return

    write_to_sheet("YourGoogleSheetName", [update.effective_user.id, text])
    await update.message.reply_text("Saved to Google Sheet successfully!")
