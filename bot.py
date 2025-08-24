import telebot, random, re, time, requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ✅ Bot Token
TOKEN = "8219462519:AAGP1qqMA0sP_q2yIHtx6ekTLaf2DAxLuzk"
bot = telebot.TeleBot(TOKEN)

# ✅ Luhn Algorithm
def luhn(card):
    nums = [int(x) for x in card]
    return (sum(nums[-1::-2]) + sum(sum(divmod(2 * x, 10)) for x in nums[-2::-2])) % 10 == 0

# ✅ Generate credit card number
def generate_card(bin_format):
    bin_format = bin_format.lower()
    if len(bin_format) < 16:
        bin_format += "x" * (16 - len(bin_format))
    else:
        bin_format = bin_format[:16]
    while True:
        cc = ''.join(str(random.randint(0, 9)) if x == 'x' else x for x in bin_format)
        if luhn(cc):
            return cc

# ✅ Generate card info block
def generate_output(bin_input, username):
    parts = bin_input.split("|")
    bin_format = parts[0] if len(parts) > 0 else ""
    mm_input = parts[1] if len(parts) > 1 and parts[1] != "xx" else None
    yy_input = parts[2] if len(parts) > 2 and parts[2] != "xxxx" else None
    cvv_input = parts[3] if len(parts) > 3 and parts[3] != "xxx" else None

    bin_clean = re.sub(r"[^\d]", "", bin_format)[:6]

    if not bin_clean.isdigit() or len(bin_clean) < 6:
        return f"❌ Invalid BIN provided.\n\nExample:\n<code>/gen 545231xxxxxxxxxx|03|27|xxx</code>"

    scheme = "MASTERCARD" if bin_clean.startswith("5") else "VISA" if bin_clean.startswith("4") else "UNKNOWN"
    ctype = "DEBIT" if bin_clean.startswith("5") else "CREDIT" if bin_clean.startswith("4") else "UNKNOWN"

    cards = []
    start = time.time()
    for _ in range(10):
        cc = generate_card(bin_format)
        mm = mm_input if mm_input else str(random.randint(1, 12)).zfill(2)
        yy_full = yy_input if yy_input else str(random.randint(2026, 2032))
        yy = yy_full[-2:]
        cvv = cvv_input if cvv_input else str(random.randint(100, 999))
        cards.append(f"<code>{cc}|{mm}|{yy}|{cvv}</code>")
    elapsed = round(time.time() - start, 3)

    card_lines = "\n".join(cards)

    text = f"""<b>───────────────</b>
<b>Info</b> - ↯ {scheme} - {ctype}
<b>───────────────</b>
<b>Bin</b> - ↯ {bin_clean} |<b>Time</b> - ↯ {elapsed}s
<b>Input</b> - ↯ <code>{bin_input}</code>
<b>───────────────</b>
{card_lines}
<b>───────────────</b>
<b>Requested By</b> - ↯ @{username} [Free]
"""
    return text

# ✅ /start command
@bot.message_handler(commands=['start'])
def start_handler(message):
    # Save user ID
    user_id = str(message.from_user.id)
    with open("users.txt", "a+") as f:
        f.seek(0)
        if user_id not in f.read().splitlines():
            f.write(user_id + "\n")

    # Response message
    text = (
       "🤖 Bot Status: Active ✅\n\n"
        "📢 For announcements and updates, join us 👉 [here](https://t.me/hackzonetelegram)\n\n"
        "💡 Tip: To use 𝒁𝒆𝒓𝒐𝑶𝒏𝑮𝒆𝒏 ∞ in your group, make sure I'm added as admin."
    )
    bot.reply_to(message, text, parse_mode="Markdown")

# ✅ /gen command
@bot.message_handler(commands=['gen'])
def gen_handler(message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "⚠️ Example:\n<code>/gen 545231xxxxxxxxxx|03|27|xxx</code>", parse_mode="HTML")

    bin_input = parts[1].strip()
    username = message.from_user.username or "anonymous"
    text = generate_output(bin_input, username)

    btn = InlineKeyboardMarkup()
    btn.add(InlineKeyboardButton("Re-Generate ♻️", callback_data=f"again|{bin_input}"))
    bot.reply_to(message, text, parse_mode="HTML", reply_markup=btn)

# ✅ /gen button callback
@bot.callback_query_handler(func=lambda call: call.data.startswith("again|"))
def again_handler(call):
    bin_input = call.data.split("|", 1)[1]
    username = call.from_user.username or "anonymous"
    text = generate_output(bin_input, username)

    btn = InlineKeyboardMarkup()
    btn.add(InlineKeyboardButton("Re-Generate ♻️", callback_data=f"again|{bin_input}"))

    try:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=text,
                              parse_mode="HTML",
                              reply_markup=btn)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=btn)

# ✅ /ask command (uses external GPT API)
@bot.message_handler(commands=['ask'])
def ask_handler(message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "❓ Usage: `/ask your question`", parse_mode="Markdown")
    
    prompt = parts[1]
    try:
        res = requests.get(f"https://gpt-3-5.apis-bj-devs.workers.dev/?prompt={prompt}")
        if res.status_code == 200:
            data = res.json()
            if data.get("status") and data.get("reply"):
                reply = data["reply"]
                bot.reply_to(message, f"*{reply}*", parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ Couldn't parse reply from API.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ GPT API failed to respond.", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: `{e}`", parse_mode="Markdown")

# ✅ /fake command (generate fake address)
@bot.message_handler(commands=['fake'])
def fake_address_handler(message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "⚠️ Example:\n`/fake us`", parse_mode="Markdown")

    country_code = parts[1].strip().lower()

    supported = [
        "dz","ar","au","bh","bd","be","br","kh","ca","co","dk","eg",
        "fi","fr","de","in","it","jp","kz","my","mx","ma","nz","pa",
        "pk","pe","pl","qa","sa","sg","es","se","ch","th","tr","uk",
        "us"
    ]

    if country_code not in supported:
        return bot.reply_to(message, "❌ This country is not supported or you entered an invalid code.", parse_mode="Markdown")

    url = f"https://randomuser.me/api/?nat={country_code}"
    try:
        res = requests.get(url).json()
        user = res['results'][0]

        name = f"{user['name']['first']} {user['name']['last']}"
        addr = user['location']
        full_address = f"{addr['street']['number']} {addr['street']['name']}"
        city = addr['city']
        state = addr['state']
        zip_code = addr['postcode']
        country = addr['country']

        msg = f"""📦 *Fake Address Info*

👤 *Name:* `{name}`
🏠 *Address:* `{full_address}`
🏙️ *City:* `{city}`
🗺️ *State:* `{state}`
📮 *ZIP:* `{zip_code}`
🌐 *Country:* `{country.upper()}`"""

        bot.reply_to(message, msg, parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "❌ Something went wrong. Please try again later.", parse_mode="Markdown")

# ✅ /country command
@bot.message_handler(commands=['country'])
def country_command(message):
    msg = """🌍 *Supported Countries:*

1. Algeria (DZ)
2. Argentina (AR)
3. Australia (AU)
4. Bahrain (BH)
5. Bangladesh (BD)
6. Belgium (BE)
7. Brazil (BR)
8. Cambodia (KH)
9. Canada (CA)
10. Colombia (CO)
11. Denmark (DK)
12. Egypt (EG)
13. Finland (FI)
14. France (FR)
15. Germany (DE)
16. India (IN)
17. Italy (IT)
18. Japan (JP)
19. Kazakhstan (KZ)
20. Malaysia (MY)
21. Mexico (MX)
22. Morocco (MA)
23. New Zealand (NZ)
24. Panama (PA)
25. Pakistan (PK)
26. Peru (PE)
27. Poland (PL)
28. Qatar (QA)
29. Saudi Arabia (SA)
30. Singapore (SG)
31. Spain (ES)
32. Sweden (SE)
33. Switzerland (CH)
34. Thailand (TH)
35. Turkiye (TR)
36. United Kingdom (UK)
37. United States (US)"""
    bot.reply_to(message, msg, parse_mode="Markdown")

# ✅ Broadcast command (only for bot owner)
OWNER_ID = 6474875001   

@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if message.from_user.id != OWNER_ID:
        return bot.reply_to(message, "🚫 You are not authorized to use this command.")

    try:
        _, text = message.text.split(" ", 1)
    except:
        return bot.reply_to(message, "⚠️ Usage:\n`/broadcast Your message here`", parse_mode="Markdown")

    bot.reply_to(message, "📢 Sending broadcast to all users...")

    try:
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
    except FileNotFoundError:
        return bot.send_message(message.chat.id, "❌ No users found in users.txt")

    sent, failed = 0, 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 *Broadcast Message:*\n\n{text}", parse_mode="Markdown")
            sent += 1
            time.sleep(0.1)
        except Exception as e:
            failed += 1
            continue

    bot.send_message(
        message.chat.id,
        f"✅ Broadcast completed.\n\n🟢 Sent: `{sent}`\n🔴 Failed: `{failed}`",
        parse_mode="Markdown"
    )
print("🤖 Bot is running...")
bot.polling()
