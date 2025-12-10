import logging
import os
import json
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 1. Logging ကို ဖွင့်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# 2. Global Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
GSPREAD_CREDS = os.environ.get("GSPREAD_CREDS") # Render က JSON Key
# GSPREAD_CREDS ကို မထည့်ရင် Error ပြပါလိမ့်မယ်
if not BOT_TOKEN or not GSPREAD_CREDS:
    raise ValueError("BOT_TOKEN သို့မဟုတ် GSPREAD_CREDS environment variable ကို ထည့်သွင်းပေးရန် လိုအပ်ပါသည်။")

# --- Google Sheets Configuration ---

# **အရေးကြီး:** သင်ပေးပို့လိုက်သော Sheet ID ကို ဤနေရာတွင် ထည့်သွင်းပါ
SHEET_ID = "1jjPtDpsUOToRR4CuZM1ap37LMAR_imF44QEmfT6t24c" 
worksheet = None # Global Worksheet instance

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

# --- Google Sheet Helper Functions ---

def setup_gsheet():
    """Google Sheet ကို Service Account ဖြင့် ချိတ်ဆက်ခြင်း"""
    global worksheet
    
    # Environment Variable ကနေ JSON စာသားကို ယူပြီး Dictionary အဖြစ် ပြောင်းလဲခြင်း
    try:
        creds = json.loads(GSPREAD_CREDS)
        
        # Service Account ကို authorize လုပ်ခြင်း
        gc = gspread.service_account_from_dict(creds)
        
        # Sheet ကို ID ဖြင့် ဖွင့်ခြင်း
        spreadsheet = gc.open_by_key(SHEET_ID)
        
        # ပထမဆုံး Sheet (Worksheet) ကို ရယူခြင်း
        worksheet = spreadsheet.sheet1 
        print("Google Sheet setup complete.")

    except Exception as e:
        print(f"Google Sheet connection error: {e}")
        # Connection Failed ဖြစ်ရင် Bot ကို ရပ်တန့်ဖို့အတွက် Exception ထုတ်
        raise

def save_new_user_to_sheet(user_id, username, first_name):
    """User Data ကို Sheet ထဲတွင် ထည့်သွင်းခြင်း (Duplication ကို စစ်ဆေးသည်)"""
    if worksheet is None:
        # worksheet မရှိသေးရင် အရင်ဆုံး ချိတ်ဆက်ပါ
        setup_gsheet()

    try:
        # User_id သည် ရှိပြီးသားလား စစ်ဆေးရန် (Column A)
        # ကြီးမားသော Sheet များအတွက် အချိန်ကြာနိုင်ပါသည်။
        user_ids = [str(x) for x in worksheet.col_values(1)] 
        
        if str(user_id) not in user_ids:
            # အချက်အလက်အသစ်ကို List အဖြစ် ဖန်တီးခြင်း
            new_row = [
                user_id,
                username if username else "",
                first_name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            
            # Sheet ရဲ့ အောက်ဆုံးအတန်းမှာ ထည့်သွင်းခြင်း
            worksheet.append_row(new_row)
            print(f"User {user_id} saved to Google Sheet.")
        # else: User ရှိပြီးသားဖြစ်သောကြောင့် ဘာမှ မလုပ်ပါ
        
    except Exception as e:
        print(f"Error saving user {user_id} to sheet: {e}")
        # Error ဖြစ်ရင် Bot ကို ဆက် run နေစေရန်အတွက် Pass လုပ်
        pass 

# --- ---

# 3. /start command အတွက် Function (User Data သိမ်းဆည်းခြင်း ပါဝင်သည်)
async def start(update: Update, context):
    user = update.effective_user
    user_id = user.id
    username = user.username if user.username else None
    first_name = user.first_name if user.first_name else "အမည်မသိသူ"
    
    # Google Sheet ထဲမှာ User ကို ထည့်သွင်းခြင်း
    save_new_user_to_sheet(user_id, username, first_name)
    
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

# 4. Inline Keyboard Button နှိပ်ခြင်းကို စီမံခန့်ခွဲတဲ့ Function
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

# 5. Reply Keyboard Button များအတွက် Message Handler
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
    
    # Bot စတင်ချိန်မှာ Google Sheet ကို ချိတ်ဆက်ခြင်း
    try:
        setup_gsheet()
    except Exception as e:
        print("Bot failed to start due to Sheet connection error.")
        return # ချိတ်ဆက်မှု မအောင်မြင်ရင် Bot မစပါ
        
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(premium_prices|star_prices|back_to_main)$"))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

