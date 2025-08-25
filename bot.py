import re
import requests
import datetime
import threading
import os
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIG ---
BOT_TOKEN = "8355095322:AAFGHc_xe7OgXufsuttz2GBarudEgy55_Lc"
API_URLS = [
    "https://ravenxchecker.site/num.php?num={}",     # Primary API
    "http://xploide.site/Api.php?num={}"            # Secondary API (fallback)
]
DAILY_LIMIT = 50
BOT_USERNAME = "bot"   # lowercase username for trigger matching
GROUP_ID = -1003039258661   # your group ID

# Track user API usage
user_usage = {}

# --- HELPERS ---
def is_trigger_message(text: str):
    pattern = rf"@{BOT_USERNAME} (\d{{10}})"
    match = re.match(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None

def is_invalid_message(text: str):
    if re.search(r"@\w+", text) and f"@{BOT_USERNAME}".lower() not in text.lower():
        return True
    if re.search(r"https?://", text):
        return True
    return False

def format_api_response(data):
    try:
        results = data if isinstance(data, list) else [data]
        formatted = []
        for entry in results:
            formatted.append(
                f"📌 Name: {entry.get('name','N/A')}\n"
                f"📱 Mobile: {entry.get('mobile','N/A')}\n"
                f"👤 Father: {entry.get('father_name','N/A')}\n"
                f"🏠 Address: {entry.get('address','N/A')}\n"
                f"🔢 ID: {entry.get('id_number','N/A')}\n"
                f"📧 Email: {entry.get('email','N/A')}\n"
                f"───────────────"
            )
        return "\n".join(formatted)
    except Exception:
        return "❌ Error formatting API response."

def fetch_from_apis(number: str):
    """Try APIs one by one until data is found."""
    for url in API_URLS:
        try:
            response = requests.get(url.format(number), timeout=5)
            data = response.json()
            if data and data != {} and data != []:
                return format_api_response(data)
        except Exception:
            continue
    return "❌ No data found from any API."

# --- HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_usage
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    text = update.message.text.strip()

    # ❌ Private chat -> Group link send
    if chat_type == "private":
        keyboard = [[InlineKeyboardButton("👉 Join Group 👈", url="https://t.me/hack_zone2")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ This bot works only in our group.\nClick below to join 👇",
            reply_markup=reply_markup
        )
        return

    # Delete invalid messages
    if is_invalid_message(text):
        await update.message.delete()
        return

    # Check trigger
    number = is_trigger_message(text)
    if number:
        today = datetime.date.today()

        if user_id not in user_usage or user_usage[user_id]["date"] != today:
            user_usage[user_id] = {"date": today, "count": 0}

        if user_usage[user_id]["count"] >= DAILY_LIMIT:
            await update.message.reply_text("⚠️ Daily API call limit reached (5). Try again tomorrow.")
            return

        # Show loading message
        loading_msg = await update.message.reply_text("⏳ Fetching data from server, please wait...")

        # Fetch data from APIs
        result = fetch_from_apis(number)

        # Increase usage
        user_usage[user_id]["count"] += 1
        remaining = DAILY_LIMIT - user_usage[user_id]["count"]

        # Delete loading message
        try:
            await loading_msg.delete()
        except:
            pass

        await update.message.reply_text(f"{result}\n\n🎯 Remaining limit: {remaining}/{DAILY_LIMIT}")

# --- FLASK WEB SERVER (for deployment health check) ---
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "✅ Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)

# --- START TELEGRAM BOT ---
def start_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Telegram Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    # Start Flask server in background thread
    threading.Thread(target=run_flask).start()
    # Start Telegram bot
    start_bot()
