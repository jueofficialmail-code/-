import logging
import os
import json
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 1. Logging ကို ဖွင့်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# 2. Global Variables (Environment Variables မှ လုံခြုံစွာ ခေါ်ယူခြင်း)
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
GSPREAD_CREDS = os.environ.get("GSPREAD_CREDS")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID") # Render Environment မှ ယူသည်

# အရေးကြီးသော Variables များ မပြည့်စုံပါက Error ပြခြင်း
if not all([BOT_TOKEN, GSPREAD_CREDS, ADMIN_CHAT_ID]):
    missing_vars = [name for name, val in [("BOT_TOKEN", BOT_TOKEN), ("GSPREAD_CREDS", GSPREAD_CREDS), 
                                           ("ADMIN_CHAT_ID", ADMIN_CHAT_ID)] if not val]
    raise ValueError(f"Environment variables မပြည့်စုံပါ: {', '.join(missing_vars)}။")

# --- Google Sheets Configuration ---
SHEET_ID = "1jjPtDpsUOToRR4CuZM1ap37LMAR_imF44QEmfT6t24c" 
USER_WORKSHEET = None # Sheet1 - User Data
SETTINGS_WORKSHEET = None # Sheet2 - Settings Data ('Settings' လို့ နာမည်ပေးထားရမည်)

# --- Coin စနစ်နှင့် ဈေးနှုန်း အချက်အလက်များ (Fixed Data) ---
COIN_PACKS = {
    100: 2000, # 100 Coin = 2000 MMK
    500: 9000, # 500 Coin = 9000 MMK
    1000: 17000 # 1000 Coin = 17000 MMK
}

# --- Google Sheet Helper Functions ---

def setup_gsheet():
    """Google Sheet ကို ချိတ်ဆက်ခြင်းနှင့် Worksheet နှစ်ခုလုံးကို ရယူခြင်း"""
    global USER_WORKSHEET, SETTINGS_WORKSHEET
    try:
        creds = json.loads(GSPREAD_CREDS)
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_key(SHEET_ID)
        
        USER_WORKSHEET = spreadsheet.sheet1 # Sheet1 ကို User Data အဖြစ် သုံးသည်
        # 'Settings' Sheet ကို Name ဖြင့် ခေါ်သည်
        SETTINGS_WORKSHEET = spreadsheet.worksheet("Settings") 
        
        print("Google Sheet setup complete. (User Data & Settings)")
    except gspread.exceptions.WorksheetNotFound:
        print("Error: 'Settings' sheet ကို ရှာမတွေ့ပါ။ သင့် Sheet ထဲမှာ Sheet အသစ်တစ်ခုကို 'Settings' လို့ နာမည်ပြောင်းပေးပါ။")
        raise
    except Exception as e:
        print(f"Google Sheet connection error: {e}")
        raise

def get_user_row(user_id):
    """USER_WORKSHEET (Sheet1) ထဲမှ အတန်းတစ်ခုလုံးကို ရှာဖွေခြင်း"""
    if USER_WORKSHEET is None: setup_gsheet()
    try:
        user_ids = [str(x) for x in USER_WORKSHEET.col_values(1)]
        if str(user_id) in user_ids:
            row_index = user_ids.index(str(user_id)) + 1
            return USER_WORKSHEET.row_values(row_index), row_index
    except Exception as e:
        print(f"Error retrieving user {user_id}: {e}")
    return None, None

def save_new_user(user_id, username, first_name):
    """User အသစ်ကို Coin 0 ဖြင့် ထည့်သွင်းခြင်း"""
    if USER_WORKSHEET is None: setup_gsheet()
    user_data, row_index = get_user_row(user_id)
    if user_data is None:
        new_row = [user_id, username if username else "", first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0]
        try:
            USER_WORKSHEET.append_row(new_row)
            print(f"User {user_id} saved with 0 coins.")
        except Exception as e:
            print(f"Error saving new user: {e}")

def get_coin_balance(user_id):
    """လက်ရှိ Coin Balance ကို ပြန်လည်ရယူခြင်း"""
    user_data, _ = get_user_row(user_id)
    if user_data and len(user_data) > 4 and user_data[4].isdigit():
        return int(user_data[4])
    return 0
    
def update_coin_balance(user_id, amount):
    """User ရဲ့ Coin Balance ကို ပြောင်းလဲခြင်း (တိုး/လျော့)"""
    if USER_WORKSHEET is None: setup_gsheet()
    user_data, row_index = get_user_row(user_id)
    if user_data is None: return False, "User ကို Database တွင် ရှာမတွေ့ပါ။"
    try:
        current_balance = int(user_data[4]) if len(user_data) > 4 and user_data[4].isdigit() else 0
        new_balance = current_balance + amount
        if new_balance < 0: return False, "Coin လက်ကျန် မလုံလောက်ပါ။"
        # Column E (5) မှာ Coin ကို Update လုပ်ခြင်း
        USER_WORKSHEET.update_cell(row_index, 5, new_balance)
        return True, new_balance
    except Exception as e:
        print(f"Error updating coin balance for {user_id}: {e}")
        return False, "Coin Update လုပ်ရာတွင် အမှားဖြစ်ပွားပါသည်။"

# --- Setting Control Functions ---
def get_setting(key):
    """Settings Sheet ကနေ Value ကို ရယူခြင်း"""
    if SETTINGS_WORKSHEET is None: setup_gsheet()
    try:
        cell = SETTINGS_WORKSHEET.find(key, in_column=1)
        if cell:
            return SETTINGS_WORKSHEET.cell(cell.row, 2).value
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
    return None

def set_setting(key, value):
    """Settings Sheet ထဲမှာ Value ကို ပြောင်းလဲခြင်း"""
    if SETTINGS_WORKSHEET is None: setup_gsheet()
    try:
        cell = SETTINGS_WORKSHEET.find(key, in_column=1)
        if cell:
            SETTINGS_WORKSHEET.update_cell(cell.row, 2, value)
            return True
    except Exception as e:
        print(f"Error setting value for {key}: {e}")
    return False

# --- Helper Function for Payment Details (Settings Sheet မှ ယူရန် ပြင်ဆင်) ---

async def get_payment_details():
    """Settings Sheet မှ Payment Details အားလုံးကို Real-time ရယူခြင်း"""
    kpay_phone = get_setting("K_PAY_PHONE")
    wave_phone = get_setting("WAVE_PAY_PHONE")
    kbz_name = get_setting("KBZ_NAME")
    wave_name = get_setting("WAVE_NAME")
    
    return {
        "kpay": {"name": kbz_name or "Unknown", "phone": kpay_phone or "N/A", "bank_name": "KBZPay"},
        "wave": {"name": wave_name or "Unknown", "phone": wave_phone or "N/A", "bank_name": "WavePay"}
    }
    
# --- 3. /start command အတွက် Function (NameError ကို ဖြေရှင်းပေးသည်) ---
async def start(update: Update, context):
    user = update.effective_user
    save_new_user(user.id, user.username, user.first_name)
    
    # Inline Keyboard (Premium / Star ရွေးချယ်ရန်)
    inline_keyboard = [
        [
            InlineKeyboardButton("💎 Telegram Premium", callback_data="premium_prices"),
            InlineKeyboardButton("🌟 Telegram Star", callback_data="star_prices"),
        ]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    # Reply Keyboard (အမြဲတမ်း ပေါ်နေမည့် Buttons)
    reply_keyboard = [
        [KeyboardButton("💰 Coin ဈေးနှုန်းများ"), KeyboardButton("👤 User Account")],
        [KeyboardButton("❓ Help Center")]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"👋 **{user.first_name}**၊ ကျွန်မရဲ့ ဝန်ဆောင်မှုများကို ရွေးချယ်နိုင်ပါတယ်:",
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="အောက်ဘက်ရှိ Buttons များသည် အမြဲတမ်း ပေါ်နေပါမည်။",
        reply_markup=reply_markup
    )

# --- 4. Reply Keyboard Button များအတွက် Message Handler ---
async def handle_message(update: Update, context):
    text = update.message.text
    user = update.effective_user
    response = ""

    if text == "💰 Coin ဈေးနှုန်းများ":
        coin_message = "💰 **Coin ဈေးနှုန်းများ (MMK):**\n\n"
        for coin, price in COIN_PACKS.items():
            coin_message += f"• **{coin} Coin** = `{price} MMK`\n"
        
        coin_message += "\nငွေပေးချေရန် နည်းလမ်းကို ရွေးချယ်ပါ:"
        
        payment_keyboard = [[InlineKeyboardButton("KBZPay (KPay)", callback_data="pay_kpay")],
                            [InlineKeyboardButton("WavePay (Wave)", callback_data="pay_wave")]]
        
        await update.message.reply_text(coin_message, 
                                        reply_markup=InlineKeyboardMarkup(payment_keyboard), 
                                        parse_mode="Markdown")
        return 

    elif text == "👤 User Account":
        # Coin Balance ကို Sheet ကနေ ဆွဲယူပြီး ပြသခြင်း
        balance = get_coin_balance(user.id) 
        response = (f"👤 **{user.first_name}** ၏ Account အချက်အလက်များ:\n\n"
                    f"💰 **လက်ရှိ Coin Balance:** `{balance}` Coin\n"
                    "\nဝန်ဆောင်မှုများကို Coin ဖြင့် ဝယ်ယူနိုင်ပါတယ်:")
    
    elif text == "❓ Help Center":
        response = ("❓ **Help Center:**\n\n"
                    "အကူအညီ လိုအပ်ပါက ဆက်သွယ်ရန်: @MeowHelpCenterBot")
    
    else:
        response = f"ကျွန်မက '{text}' ဆိုတဲ့ စာကို နားမလည်ပါဘူး။"

    await update.message.reply_text(response, parse_mode="Markdown")
    
# --- 5. 💰 ငွေပေးချေမှု ပြေစာကို လက်ခံခြင်းနှင့် Admin သို့ Noti ပို့ခြင်း Function ---
async def handle_photo(update: Update, context):
    user = update.effective_user
    
    response = ("✅ **ပြေစာကို လက်ခံရရှိပါပြီ!**\n\n"
                "ကျွန်မတို့ စစ်ဆေးပြီး Coin Balance ကို အမြန်ဆုံး တိုးပေးပါမယ်။\n"
                "စောင့်ဆိုင်းပေးပါရန် မေတ္တာရပ်ခံပါတယ်ရှင်။")
    
    await update.message.reply_text(response, parse_mode="Markdown")

    # Admin ကို Noti ပို့မည့် စာသား
    admin_noti = (
        "🚨 **ငွေလွှဲပြေစာ အသစ် ရောက်ရှိလာပါပြီ** 🚨\n\n"
        f"👤 User ID: `{user.id}`\n"
        f"🙋‍♂️ Username: @{user.username or 'N/A'}\n"
        "Coin Balance ကို **Sheet ထဲမှာ Manual Update** လုပ်ပေးရန် လိုအပ်ပါသည်။"
    )
    
    try:
        # ဓာတ်ပုံကို Admin Chat ID သို့ ပို့ပေးခြင်း
        photo_file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID, 
            photo=photo_file_id,
            caption=admin_noti,
            parse_mode="Markdown"
        )
        print(f"Admin notified about payment from User {user.id}")
        
    except Exception as e:
        print(f"Could not send photo to Admin: {e}")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, 
            text=f"⚠️ **Error!** User {user.id} က ငွေလွှဲပြေစာ ပို့ခဲ့ပါတယ်၊ ဒါပေမဲ့ ပုံပို့ရာမှာ Error ဖြစ်လို့ စာသားသက်သက်သာ ရောက်ရှိပါတယ်။",
            parse_mode="Markdown"
        )

# --- 6. Inline Keyboard Button နှိပ်ခြင်းကို စီမံခန့်ခွဲတဲ့ Function ---
async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data
    
    # Settings Sheet ကနေ Real-time Details ကို ရယူခြင်း
    payment_details = await get_payment_details() 
    
    # --- Payment Button နှိပ်ခြင်း ---
    if data in ["pay_kpay", "pay_wave"]:
        method = data.split("_")[1]
        details = payment_details.get(method)
        
        message = (
            f"💳 **{details['bank_name']} ဖြင့် ငွေပေးချေရန် လမ်းညွှန်:**\n\n"
            f"👤 **အမည်:** `{details['name']}`\n"
            f"📞 **ဖုန်းနံပါတ်:** `{details['phone']}`\n\n" 
            
            "**လုပ်ဆောင်ရန်:**\n"
            "1. သင်ဝယ်ယူလိုသော Coin ဈေးနှုန်းအတိုင်း အထက်ပါ ဖုန်းနံပါတ်သို့ ငွေလွှဲပါ။\n"
            "2. ငွေလွှဲထားသော **Transaction ID** ပါဝင်သည့် **Screen Shot** ကို ကျွန်မသို့ **ပြန်ပို့ပေးပါ**။\n"
            "3. စစ်ဆေးပြီးနောက် သင့် Coin Balance ကို တိုးပေးပါမယ်။"
        )
            
    elif data == "premium_prices":
        message = "💎 **Telegram Premium ဈေးနှုန်းများ:** (Coin ဖြင့်သာ ဝယ်ယူနိုင်သည်)"
        
    elif data == "star_prices":
        message = "🌟 **Telegram Star ဈေးနှုန်းများ:** (Coin ဖြင့်သာ ဝယ်ယူနိုင်သည်)"

    elif data == "back_to_main":
        # start function ကို ပြန်ခေါ်ခြင်းဖြင့် NameError မဖြစ်စေရန်
        return await start(query, context)
        
    else:
        message = "ရွေးချယ်မှု မှားယွင်းနေပါသည်။"

    await query.edit_message_text(
        text=message, 
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ ပင်မ Menu သို့", callback_data="back_to_main")]
        ])
    )

# --- 7. Admin Command Handlers ---

async def set_kpay_command(update: Update, context):
    """/setkpay [ဖုန်းနံပါတ်] ဖြင့် KBZPay ဖုန်းနံပါတ် ပြောင်းလဲခြင်း"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Admin Command ဖြစ်ပါတယ်။")
        
    try:
        new_phone = context.args[0].strip()
        success = set_setting("K_PAY_PHONE", new_phone)
        
        if success:
            await update.message.reply_text(f"✅ KBZPay ဖုန်းနံပါတ်ကို **{new_phone}** သို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ။")
        else:
            await update.message.reply_text("❌ ပြောင်းလဲရန် Settings Sheet ထဲတွင် Key: 'K_PAY_PHONE' မရှိပါ။")
            
    except IndexError:
        await update.message.reply_text("❌ ဖုန်းနံပါတ် ထည့်သွင်းရန် လိုအပ်ပါသည်။ (ဥပမာ: /setkpay 09xxxxxxxxx)")

async def set_wave_command(update: Update, context):
    """/setwave [ဖုန်းနံပါတ်] ဖြင့် WavePay ဖုန်းနံပါတ် ပြောင်းလဲခြင်း"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Admin Command ဖြစ်ပါတယ်။")
        
    try:
        new_phone = context.args[0].strip()
        success = set_setting("WAVE_PAY_PHONE", new_phone)
        
        if success:
            await update.message.reply_text(f"✅ WavePay ဖုန်းနံပါတ်ကို **{new_phone}** သို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ။")
        else:
            await update.message.reply_text("❌ ပြောင်းလဲရန် Settings Sheet ထဲတွင် Key: 'WAVE_PAY_PHONE' မရှိပါ။")
            
    except IndexError:
        await update.message.reply_text("❌ ဖုန်းနံပါတ် ထည့်သွင်းရန် လိုအပ်ပါသည်။ (ဥပမာ: /setwave 09xxxxxxxxx)")


# 8. Main Function (Bot ကို စတင် အလုပ်လုပ်စေရန်)
def main():
    """Bot ကို စတင်ခြင်း"""
    
    # 1. Google Sheet ချိတ်ဆက်ခြင်း (Error ဖြစ်ရင် Bot ရပ်မည်)
    try:
        setup_gsheet()
    except Exception as e:
        print("Bot failed to start due to Sheet connection error.")
        return 
        
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 2. Command Handlers
    application.add_handler(CommandHandler("start", start)) # NameError ပြေလည်
    application.add_handler(CommandHandler("setkpay", set_kpay_command)) 
    application.add_handler(CommandHandler("setwave", set_wave_command)) 
    
    # 3. Message/Callback Handlers
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo)) # ဓာတ်ပုံ (ပြေစာ) လက်ခံခြင်း

    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

