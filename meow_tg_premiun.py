import logging
import os
import psycopg2 # PostgreSQL Database driver
from psycopg2 import sql 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 1. Logging ကို ဖွင့်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# 2. Global Variables
# BOT_TOKEN နှင့် DATABASE_URL ကို Render Settings (Environment Variables) ကနေ ဆွဲယူသုံးခြင်း
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
DATABASE_URL = os.environ.get("DATABASE_URL")

if not BOT_TOKEN or not DATABASE_URL:
    raise ValueError("BOT_TOKEN သို့မဟုတ် DATABASE_URL environment variable ကို ထည့်သွင်းပေးရန် လိုအပ်ပါသည်။")

# --- ဈေးနှုန်း အချက်အလက်များ ---
PREMIUM_PRICES = {
    "1_month": "4.99 USD",
    "3_month": "13.99 USD (လျှော့ဈေး)",
    "1_year": "47.99 USD (20% လျှော့ဈေး)",
}

STAR_PRICES = {
    "100_star": "2.00 USD",
    "500_star": "9.50 USD",
    "1000_star": "18.00 USD",
}
# --- ---

# --- Database Helper Functions ---

def get_db_connection():
    """Database Connection ကို ရယူခြင်း (Render PostgreSQL အတွက် SSL ပါဝင်သည်)"""
    # sslmode='require' သည် Render Database ချိတ်ဆက်မှုများအတွက် လိုအပ်ပါသည်။
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def setup_database():
    """Database ထဲမှာ 'users' table ကို ဖန်တီးခြင်း"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # users table ကို ဖန်တီးခြင်း (user_id ကို Primary Key အဖြစ် သတ်မှတ်သည်)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(50),
                first_name VARCHAR(50) NOT NULL,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        print("Database setup complete: 'users' table is ready.")
        
    except (Exception, psycopg2.Error) as error:
        print("Database setup error:", error)
    finally:
        if conn:
            conn.close()

def save_new_user(user_id, username, first_name):
    """User အသစ်ကို Database ထဲသို့ ထည့်သွင်းခြင်း (user_id ရှိပြီးသားဆိုရင် ကျော်သွားမည်)"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # ON CONFLICT DO NOTHING ကို သုံးခြင်းဖြင့် ရှိပြီးသား User ကို ထပ်မထည့်တော့ဘဲ ရှောင်ရှားသည်
        cur.execute("""
            INSERT INTO users (user_id, username, first_name) 
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING;
        """, (user_id, username, first_name))
        
        conn.commit()
        cur.close()
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error saving user {user_id}:", error)
    finally:
        if conn:
            conn.close()

# --- ---

# 3. /start command အတွက် Function
async def start(update: Update, context):
    """/start command နှိပ်ရင် ပထမဆုံး မက်ဆေ့ချ်၊ Inline Keyboard နဲ့ Reply Keyboard ကို ပို့ပေးတဲ့ function"""
    
    # User ရဲ့ အချက်အလက်များကို ရယူခြင်း
    user = update.effective_user
    user_id = user.id
    username = user.username if user.username else None
    first_name = user.first_name if user.first_name else "အမည်မသိသူ"
    
    # ဤနေရာတွင် User Data ကို Database ထဲသို့ ထည့်သွင်းခြင်း
    save_new_user(user_id, username, first_name)
    
    # --- Inline Keyboard (Premium / Star ရွေးချယ်ရန်) ---
    inline_keyboard = [
        [
            InlineKeyboardButton("💎 Telegram Premium", callback_data="premium_prices"),
            InlineKeyboardButton("🌟 Telegram Star", callback_data="star_prices"),
        ]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    # --- Reply Keyboard (အမြဲတမ်း ပေါ်နေမည့် Buttons) ---
    reply_keyboard = [
        [KeyboardButton("👤 User Account"), KeyboardButton("❓ Help Center")],
        [KeyboardButton("💳 Payment Methods")]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)

    # Message ပို့ခြင်း
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"👋 **{first_name}**၊ ကျွန်မရဲ့ Telegram ဝန်ဆောင်မှုများကို ရွေးချယ်နိုင်ပါတယ်:",
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="အောက်ဘက်ရှိ Buttons များသည် အမြဲတမ်း ပေါ်နေပါမည်။",
        reply_markup=reply_markup
    )

# 4. Inline Keyboard Button နှိပ်ခြင်းကို စီမံခန့်ခွဲတဲ့ Function (ယခင်အတိုင်း)
async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data
    message = ""
    
    if data == "premium_prices":
        message = "💎 **Telegram Premium ဈေးနှုန်းများ:**\n\n"
        for key, value in PREMIUM_PRICES.items():
            message += f"• {key.replace('_', ' ').title()}: `{value}`\n"
    
    elif data == "star_prices":
        message = "🌟 **Telegram Star ဈေးနှုန်းများ:**\n\n"
        for key, value in STAR_PRICES.items():
            message += f"• {key.replace('_', ' ').title()}: `{value}`\n"
    
    elif data == "back_to_main":
        await query.edit_message_text(
            text="👋 **ကြိုဆိုပါတယ်!** ကျွန်မရဲ့ Telegram ဝန်ဆောင်မှုများကို ရွေးချယ်နိုင်ပါတယ်:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Telegram Premium", callback_data="premium_prices"),
                 InlineKeyboardButton("🌟 Telegram Star", callback_data="star_prices")]
            ]),
            parse_mode="Markdown"
        )
        return

    await query.edit_message_text(
        text=message, 
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ နောက်သို့ ပြန်သွားရန်", callback_data="back_to_main")]
        ])
    )

# 5. Reply Keyboard Button များအတွက် Message Handler (ယခင်အတိုင်း)
async def handle_message(update: Update, context):
    text = update.message.text

    if text == "👤 User Account":
        response = (
            "👤 **User Account အချက်အလက်များ:**\n\n"
            "ကျွန်မရဲ့ account ကို စီမံခန့်ခွဲဖို့အတွက် အောက်ပါအတိုင်း လိုက်နာဆောင်ရွက်နိုင်ပါတယ်:\n"
            "• Settings > Privacy and Security\n" 
            "• Settings > Data and Storage"
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
        response = f"ကျွန်မက '{text}' ဆိုတဲ့ စာကို နားမလည်ပါဘူး။ အပေါ်က Button များကို အသုံးပြုပေးပါ။"

    await update.message.reply_text(response, parse_mode="Markdown")

# 6. Main Function (Bot ကို စတင် အလုပ်လုပ်စေရန်)
def main():
    """Bot ကို စတင်ခြင်း"""
    
    # Database ကို စတင် setup လုပ်ခြင်း (Table ရှိမရှိ စစ်ဆေးပြီး မရှိရင် ဖန်တီးသည်)
    setup_database()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers များ
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(premium_prices|star_prices|back_to_main)$"))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Bot ကို စတင် run ခြင်း (Polling mode ဖြင့်)
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

