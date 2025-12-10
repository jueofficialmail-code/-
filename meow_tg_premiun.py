import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 1. Logging ကို ဖွင့်ခြင်း (အဆင်မပြေမှုများကို စစ်ဆေးရန်)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
# logger = logging.getLogger(__name__)

# 2. Global Variables
# *** ဒီနေရာမှာ ကိုယ့်ရဲ့ Bot Token ကို ထည့်သွင်းပါ ***
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" 

# 3. /start command အတွက် Function
async def start(update: Update, context):
    """/start command နှိပ်ရင် ပထမဆုံး မက်ဆေ့ချ်နဲ့ Inline Keyboard ကို ပို့ပေးတဲ့ function"""

    # Inline Keyboard ကို ဖန်တီးခြင်း
    # Premium နဲ့ Star ကို ခွဲခြားဖို့ callback_data ကို သုံးပါတယ်။
    keyboard = [
        [
            InlineKeyboardButton("Telegram Premium", callback_data="premium_prices"),
            InlineKeyboardButton("Telegram Star", callback_data="star_prices"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Reply Keyboard (စာရိုက်တဲ့နေရာက buttons) ကို ဖန်တီးခြင်း
    reply_keyboard = [
        [KeyboardButton("User Account"), KeyboardButton("Help Center")]
    ]
    custom_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)

    # မက်ဆေ့ချ် ပို့ခြင်း
    await update.message.reply_text(
        "👋 **ကြိုဆိုပါတယ်!** ကျွန်မရဲ့ Telegram ဝန်ဆောင်မှု အချက်အလက်များကို ရွေးချယ်နိုင်ပါတယ်:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    # Reply Keyboard ကိုလည်း တစ်ပြိုင်နက်တည်း ပို့ပေးခြင်း
    await update.message.reply_text(
        "အောက်ဘက်ရှိ (စာရိုက်တဲ့နေရာ) buttons များက အမြဲတမ်း ပေါ်နေပါမည်။",
        reply_markup=custom_markup
    )

# 4. Inline Keyboard Button နှိပ်ခြင်းကို စီမံခန့်ခွဲတဲ့ Function
async def button_callback(update: Update, context):
    """Inline Keyboard Buttons များ နှိပ်လိုက်သောအခါ လုပ်ဆောင်မယ့် function"""

    query = update.callback_query
    
    # query ကို ဖြေရှင်းခြင်း (Loading icon ပျောက်သွားအောင်)
    await query.answer()

    data = query.data
    
    # ဈေးနှုန်း အချက်အလက်များ
    if data == "premium_prices":
        message = (
            "💎 **Telegram Premium ဈေးနှုန်းများ:**\n\n"
            "   * တစ်လ: 4.99 USD\n"
            "   * ခြောက်လ: 26.99 USD\n"
            "   * တစ်နှစ်: 47.99 USD (20% လျှော့စျေး)"
        )
    elif data == "star_prices":
        message = (
            "🌟 **Telegram Star ဈေးနှုန်းများ:**\n\n"
            "   * 100 Stars: 2.00 USD\n"
            "   * 500 Stars: 9.50 USD\n"
            "   * 1000 Stars: 18.00 USD"
        )
    else:
        message = "ရွေးချယ်မှု မှားယွင်းနေပါသည်။"

    # မူလ မက်ဆေ့ချ်ကို ပြင်ဆင်ပြီး အဖြေကို ပို့ခြင်း
    # context.bot.edit_message_text( ကိုသုံးမယ့်အစား
    # query.edit_message_text ကို သုံးပြီး လွယ်လွယ်ကူကူ မက်ဆေ့ချ်ကို ပြင်လိုက်ပါတယ်။
    await query.edit_message_text(
        text=message, 
        parse_mode="Markdown",
        # ဈေးနှုန်း ပြပြီးနောက် မူလ ရွေးချယ်မှု မက်ဆေ့ချ်ဆီ ပြန်သွားနိုင်ဖို့ Button ထည့်မယ်
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ နောက်သို့ ပြန်သွားရန်", callback_data="back_to_main")]
        ])
    )

# 5. နောက်သို့ ပြန်သွားတဲ့ Button ကို စီမံခန့်ခွဲတဲ့ Function (လိုချင်ရင် ထပ်ထည့်ရုံပါ)
async def back_to_main(update: Update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Telegram Premium", callback_data="premium_prices"),
            InlineKeyboardButton("Telegram Star", callback_data="star_prices"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="👋 **ကြိုဆိုပါတယ်!** ကျွန်မရဲ့ Telegram ဝန်ဆောင်မှု အချက်အလက်များကို ရွေးချယ်နိုင်ပါတယ်:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# 6. Reply Keyboard Button များအတွက် Message Handler
async def handle_message(update: Update, context):
    """User က Reply Keyboard Buttons (User Account / Help Center) ကို နှိပ်ရင် တုံ့ပြန်မယ့် function"""

    text = update.message.text

    if text == "User Account":
        response = (
            "👤 **User Account အချက်အလက်များ:**\n\n"
            "ကျွန်မရဲ့ account ကို စီမံခန့်ခွဲဖို့အတွက် အောက်ပါအတိုင်း လိုက်နာဆောင်ရွက်နိုင်ပါတယ်:\n"
            "* `Settings` > `Privacy and Security`\n"
            "* `Settings` > `Data and Storage`"
        )
    elif text == "Help Center":
        response = (
            "❓ **Help Center:**\n\n"
            "အကူအညီ လိုအပ်ပါက အောက်ပါ လမ်းကြောင်းများမှ ဆက်သွယ်နိုင်ပါတယ်:\n"
            "* တရားဝင် Telegram Support: https://telegram.org/support\n"
            "* FAQ: https://telegram.org/faq"
        )
    else:
        # အခြား စာရိုက်ခြင်းများကို စီမံခန့်ခွဲခြင်း (optional)
        response = f"ကျွန်မက '{text}' ဆိုတဲ့ စာကို နားမလည်ပါဘူး။ အပေါ်က Button များကို အသုံးပြုပေးပါ။"

    await update.message.reply_text(response, parse_mode="Markdown")


# 7. Main Function (Bot ကို စတင် အလုပ်လုပ်စေရန်)
def main():
    """Bot ကို စတင်ခြင်း"""

    # ApplicationBuilder ကို အသုံးပြုပြီး Bot Application ကို ဖန်တီးခြင်း
    application = Application.builder().token(BOT_TOKEN).build()

    # Command Handler များကို ထည့်သွင်းခြင်း
    application.add_handler(CommandHandler("start", start))

    # Callback Query Handler ကို ထည့်သွင်းခြင်း (Inline Buttons များအတွက်)
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(premium_prices|star_prices)$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    
    # Message Handler ကို ထည့်သွင်းခြင်း (Reply Buttons များအတွက်)
    # filters.TEXT & (~filters.COMMAND) က စာသား မက်ဆေ့ချ်များကိုသာ စီမံခန့်ခွဲပြီး command များကို ချန်လှပ်ထားမယ်
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Bot ကို စတင် run ခြင်း
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

