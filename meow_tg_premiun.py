import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 1. Logging ကို ဖွင့်ခြင်း (အဆင်မပြေမှုများကို စစ်ဆေးရန်)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# 2. Global Variables
# BOT_TOKEN ကို Environment Variables (Render settings) ကနေ ဆွဲယူသုံးခြင်း
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
if not BOT_TOKEN:
    # Render မှာ Token မထည့်ထားရင် Error ပြပြီး Deploy မလုပ်အောင် တားဆီးခြင်း
    raise ValueError("BOT_TOKEN environment variable ကို Render တွင် ထည့်သွင်းပေးရန် လိုအပ်ပါသည်။")

# 3. /start command အတွက် Function
async def start(update: Update, context):
    """/start command နှိပ်ရင် ပထမဆုံး မက်ဆေ့ချ်၊ Inline Keyboard နဲ့ Reply Keyboard ကို ပို့ပေးတဲ့ function"""

    # --- Inline Keyboard (Premium / Star) ---
    keyboard = [
        [
            InlineKeyboardButton("Telegram Premium", callback_data="premium_prices"),
            InlineKeyboardButton("Telegram Star", callback_data="star_prices"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # --- Reply Keyboard (User Account, Help Center, နှင့် Payment) ---
    # Reply Keyboard ကို စာရိုက်တဲ့ နေရာ အောက်နားမှာ ပေါ်စေဖို့
    reply_keyboard = [
        # ပထမတန်း: User Account နှင့် Help Center
        [KeyboardButton("👤 User Account"), KeyboardButton("❓ Help Center")],
        # ဒုတိယတန်း: Payment Methods (အရှည်တစ်လုံး)
        [KeyboardButton("💳 Payment Methods")]
    ]
    custom_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)

    # မက်ဆေ့ချ် ပို့ခြင်း
    await update.message.reply_text(
        "👋 **ကြိုဆိုပါတယ်!** ကျွန်မရဲ့ Telegram ဝန်ဆောင်မှု အချက်အလက်များကို ရွေးချယ်နိုင်ပါတယ်:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "အောက်ဘက်ရှိ buttons များက အမြဲတမ်း ပေါ်နေပါမည်။",
        reply_markup=custom_markup
    )

# 4. Inline Keyboard Button နှိပ်ခြင်းကို စီမံခန့်ခွဲတဲ့ Function
async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data
    
    if data == "premium_prices":
        message = (
            "💎 **Telegram Premium ဈေးနှုန်းများ:**\n\n"
            "   * တစ်လ: 4.99 USD\n"
            "   * တစ်နှစ်: 47.99 USD"
        )
    elif data == "star_prices":
        message = (
            "🌟 **Telegram Star ဈေးနှုန်းများ:**\n\n"
            "   * 100 Stars: 2.00 USD\n"
            "   * 1000 Stars: 18.00 USD"
        )
    elif data == "back_to_main":
        # နောက်သို့ပြန်သွားရန် နှိပ်ရင် start function ကို ပြန်ခေါ်ခြင်း
        await start(query, context) 
        return
    else:
        message = "ရွေးချယ်မှု မှားယွင်းနေပါသည်။"

    # မူလ မက်ဆေ့ချ်ကို ပြင်ဆင်ပြီး အဖြေကို ပို့ခြင်း
    await query.edit_message_text(
        text=message, 
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ နောက်သို့ ပြန်သွားရန်", callback_data="back_to_main")]
        ])
    )

# 5. Reply Keyboard Button များအတွက် Message Handler
async def handle_message(update: Update, context):
    """User က Reply Keyboard Buttons နှိပ်ရင် သက်ဆိုင်ရာ အဖြေ ပေးတဲ့ function"""

    text = update.message.text

    if text == "👤 User Account":
        response = (
            "👤 **User Account အချက်အလက်များ:**\n\n"
            "ကျွန်မရဲ့ account ကို စီမံခန့်ခွဲဖို့အတွက် အောက်ပါအတိုင်း လိုက်နာဆောင်ရွက်နိုင်ပါတယ်:\n"
            "* `Settings` > `Privacy and Security`\n"
            "* `Settings` > `Data and Storage`"
        )
    
    elif text == "❓ Help Center":
        response = (
            "❓ **Help Center:**\n\n"
            "အကူအညီ လိုအပ်ပါက အောက်ပါ လမ်းကြောင်းများမှ ဆက်သွယ်နိုင်ပါတယ်:\n"
            "* FAQ: https://telegram.org/faq\n"
            "* **ဆက်သွယ်ရန်:** @MeowHelpCenterBot"
        )
    
    elif text == "💳 Payment Methods":
        response = (
            "💳 **ငွေပေးချေမှု စနစ်များ:**\n\n"
            "ကျွန်မရဲ့ ဝန်ဆောင်မှုများအတွက် အောက်ပါ နည်းလမ်းများဖြင့် ပေးချေနိုင်ပါတယ်:\n"
            "* Visa / Master Card\n"
            "* Cryptocurrency (USDT, BTC)\n"
            "* Local Mobile Banking (KBZPay / WavePay)"
        )
    
    else:
        # အခြား စာရိုက်ခြင်းများကို စီမံခန့်ခွဲခြင်း
        response = f"ကျွန်မက '{text}' ဆိုတဲ့ စာကို နားမလည်ပါဘူး။ အပေါ်က Button များကို အသုံးပြုပေးပါ။"

    await update.message.reply_text(response, parse_mode="Markdown")

# 6. Main Function (Bot ကို စတင် အလုပ်လုပ်စေရန်)
def main():
    """Bot ကို စတင်ခြင်း"""

    # BOT_TOKEN ကို အသုံးပြုပြီး Application ကို ဖန်တီးခြင်း
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers များ ထည့်သွင်းခြင်း
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(premium_prices|star_prices|back_to_main)$"))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Bot ကို စတင် run ခြင်း (Polling mode ဖြင့်)
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

