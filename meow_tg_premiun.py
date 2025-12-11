import logging
import os
import json
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ... (Logging နှင့် Global Variables များ အတူတူ) ...

# 2. Global Variables (Environment Variables မှ လုံခြုံစွာ ခေါ်ယူခြင်း)
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
GSPREAD_CREDS = os.environ.get("GSPREAD_CREDS")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID") # Admin Chat ID ကို Environment ထဲမှာ ဆက်ထားပါ

if not all([BOT_TOKEN, GSPREAD_CREDS, ADMIN_CHAT_ID]):
    raise ValueError("အရေးကြီးသော Environment variables မပြည့်စုံပါ")

# --- Google Sheets Configuration ---
SHEET_ID = "1jjPtDpsUOToRR4CuZM1ap37LMAR_imF44QEmfT6t24c" 
USER_WORKSHEET = None # Sheet1 - User Data
SETTINGS_WORKSHEET = None # Sheet2 - Settings Data

# --- Google Sheet Helper Functions ---

def setup_gsheet():
    """Google Sheet ကို ချိတ်ဆက်ခြင်းနှင့် Worksheet နှစ်ခုလုံးကို ရယူခြင်း"""
    global USER_WORKSHEET, SETTINGS_WORKSHEET
    try:
        creds = json.loads(GSPREAD_CREDS)
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_key(SHEET_ID)
        
        USER_WORKSHEET = spreadsheet.sheet1 # Sheet1 ကို User Data အဖြစ် သုံးသည်
        SETTINGS_WORKSHEET = spreadsheet.worksheet("Settings") # 'Settings' Sheet ကို Name ဖြင့် ခေါ်သည်
        
        print("Google Sheet setup complete. (User Data & Settings)")
    except gspread.exceptions.WorksheetNotFound:
        print("Error: 'Settings' sheet ကို ရှာမတွေ့ပါ။ သင့် Sheet ထဲမှာ Sheet အသစ်တစ်ခုကို 'Settings' လို့ နာမည်ပြောင်းပေးပါ။")
        raise
    except Exception as e:
        print(f"Google Sheet connection error: {e}")
        raise

# --- Setting Control Functions ---
def get_setting(key):
    """Settings Sheet ကနေ Value ကို ရယူခြင်း"""
    if SETTINGS_WORKSHEET is None: setup_gsheet()
    try:
        # Key (Col A) ကိုရှာပြီး Value (Col B) ကို ယူခြင်း
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

# --- Google Sheet Helper Functions (USER_WORKSHEET ကို အသုံးပြုရန် ပြင်ဆင်) ---

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

# ... (ကျန်တဲ့ save_new_user, get_coin_balance, update_coin_balance functions များ USER_WORKSHEET ဖြင့် အတူတူ) ...

# --- Admin Command Handlers ---

async def set_kpay_command(update: Update, context):
    """/setkpay [ဖုန်းနံပါတ်] ဖြင့် KBZPay ဖုန်းနံပါတ် ပြောင်းလဲခြင်း"""
    # Admin မှန်ကန်ကြောင်း စစ်ဆေးခြင်း
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Admin Command ဖြစ်ပါတယ်။")
        
    try:
        new_phone = context.args[0].strip()
        if not new_phone.isdigit() or len(new_phone) < 9:
            return await update.message.reply_text("❌ မှန်ကန်သော ဖုန်းနံပါတ်ကို ပေးပါ။ (ဥပမာ: /setkpay 09xxxxxxxxx)")
            
        success = set_setting("K_PAY_PHONE", new_phone)
        
        if success:
            await update.message.reply_text(f"✅ KBZPay ဖုန်းနံပါတ်ကို **{new_phone}** သို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ။")
        else:
            await update.message.reply_text("❌ ပြောင်းလဲရန် Settings Sheet ထဲတွင် Key: 'K_PAY_PHONE' မရှိပါ။")
            
    except IndexError:
        await update.message.reply_text("❌ ဖုန်းနံပါတ် ထည့်သွင်းရန် လိုအပ်ပါသည်။ (ဥပမာ: /setkpay 09xxxxxxxxx)")
    except Exception as e:
        await update.message.reply_text(f"🛑 Error ဖြစ်ပွား: {e}")

async def set_wave_command(update: Update, context):
    """/setwave [ဖုန်းနံပါတ်] ဖြင့် WavePay ဖုန်းနံပါတ် ပြောင်းလဲခြင်း"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return await update.message.reply_text("⛔ Admin Command ဖြစ်ပါတယ်။")
        
    try:
        new_phone = context.args[0].strip()
        if not new_phone.isdigit() or len(new_phone) < 9:
            return await update.message.reply_text("❌ မှန်ကန်သော ဖုန်းနံပါတ်ကို ပေးပါ။ (ဥပမာ: /setwave 09xxxxxxxxx)")
            
        success = set_setting("WAVE_PAY_PHONE", new_phone)
        
        if success:
            await update.message.reply_text(f"✅ WavePay ဖုန်းနံပါတ်ကို **{new_phone}** သို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ။")
        else:
            await update.message.reply_text("❌ ပြောင်းလဲရန် Settings Sheet ထဲတွင် Key: 'WAVE_PAY_PHONE' မရှိပါ။")
            
    except IndexError:
        await update.message.reply_text("❌ ဖုန်းနံပါတ် ထည့်သွင်းရန် လိုအပ်ပါသည်။ (ဥပမာ: /setwave 09xxxxxxxxx)")
    except Exception as e:
        await update.message.reply_text(f"🛑 Error ဖြစ်ပွား: {e}")

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
    
# --- Main Logic Functions (Settings ကို ခေါ်သုံးရန် ပြင်ဆင်) ---

# 6. Inline Keyboard Button နှိပ်ခြင်းကို စီမံခန့်ခွဲတဲ့ Function
async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data
    
    # Settings Sheet ကနေ Real-time Details ကို ရယူခြင်း
    payment_details = await get_payment_details() 
    
    # --- Payment Button နှိပ်ခြင်း ---
    if data in ["pay_kpay", "pay_wave"]:
        method = data.split("_")[1] # kpay or wave
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
            
    # ... (ကျန်တဲ့ premium_prices, star_prices, back_to_main များ အတူတူ) ...

    # Message ကို ပြန်ပို့ခြင်း
    await query.edit_message_text(
        text=message, 
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ ပင်မ Menu သို့", callback_data="back_to_main")]
        ])
    )

# ... (start, handle_message, handle_photo functions များ အတူတူ) ...


# 7. Main Function (Bot ကို စတင် အလုပ်လုပ်စေရန်)
def main():
    """Bot ကို စတင်ခြင်း"""
    
    try:
        setup_gsheet()
    except Exception as e:
        print("Bot failed to start due to Sheet connection error.")
        return 
        
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setkpay", set_kpay_command)) # Admin Command
    application.add_handler(CommandHandler("setwave", set_wave_command)) # Admin Command
    
    # Handlers
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
    
