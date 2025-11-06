import telebot
import sqlite3
from telebot import types

TOKEN = "8162229291:AAH5g9PEu3nIgPnW9E2166XYDCizYi700_c"
OWNER_ID = 7617397626

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("kino.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS films (code TEXT, file_id TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
conn.commit()

def is_subscribed(user_id):
    cur.execute("SELECT username FROM channels")
    channels = cur.fetchall()
    if not channels:
        return True
    for ch in channels:
        try:
            res = bot.get_chat_member(ch[0], user_id)
            if res.status in ["left", "kicked"]:
                return False
        except:
            pass
    return True

@bot.message_handler(commands=["start"])
def start(msg):
    user_id = msg.from_user.id
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    cur.execute("SELECT username FROM channels")
    channels = cur.fetchall()
    if channels:
        markup = types.InlineKeyboardMarkup()
        for ch in channels:
            markup.add(types.InlineKeyboardButton(text=ch[0], url=f"https://t.me/{ch[0].replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub"))
        bot.send_message(user_id, "Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling 👇", reply_markup=markup)
    else:
        bot.send_message(user_id, "🎬 Film kodini kiriting:")
        bot.register_next_step_handler(msg, get_film)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(c):
    if is_subscribed(c.from_user.id):
        bot.delete_message(c.message.chat.id, c.message.message_id)
        bot.send_message(c.from_user.id, f"Salom @{c.from_user.username or 'foydalanuvchi'}! 🎬 Film kodini kiriting:")
        bot.register_next_step_handler_by_chat_id(c.from_user.id, get_film)
    else:
        bot.answer_callback_query(c.id, "❗Avval barcha kanallarga obuna bo‘ling!")

def get_film(msg):
    code = msg.text.strip()
    cur.execute("SELECT file_id FROM films WHERE code=?", (code,))
    res = cur.fetchone()
    if res:
        bot.send_video(msg.chat.id, res[0], caption="🎬 Marhamat, film tayyor!")
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kodli film topilmadi.")

@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if msg.from_user.id == OWNER_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 Statistika", "🎞 Film joylash", "➕ Admin qo‘shish")
        markup.add("📢 Reklama", "📺 Kanal sozlash")
        bot.send_message(msg.chat.id, "Admin paneliga xush kelibsiz!", reply_markup=markup)
    else:
        cur.execute("SELECT user_id FROM admins WHERE user_id=?", (msg.from_user.id,))
        if cur.fetchone():
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("🎞 Film joylash")
            bot.send_message(msg.chat.id, "🎬 Siz film joylay olasiz!", reply_markup=markup)
        else:
            bot.send_message(msg.chat.id, "Siz admin emassiz.")

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(msg):
    if msg.from_user.id == OWNER_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM films")
        films = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM admins")
        admins = cur.fetchone()[0]
        bot.send_message(msg.chat.id, f"👥 Foydalanuvchilar: {users}\n🎞 Filmlar: {films}\n👑 Adminlar: {admins}")

@bot.message_handler(func=lambda m: m.text == "🎞 Film joylash")
def upload_film(msg):
    bot.send_message(msg.chat.id, "🎬 Film kodini kiriting:")
    bot.register_next_step_handler(msg, get_code)

def get_code(msg):
    code = msg.text.strip()
    bot.send_message(msg.chat.id, "🎥 Endi filmni MP4 shaklda yuboring:")
    bot.register_next_step_handler(msg, save_film, code)

def save_film(msg, code):
    if msg.video:
        file_id = msg.video.file_id
        cur.execute("INSERT INTO films (code, file_id) VALUES (?,?)", (code, file_id))
        conn.commit()
        bot.send_message(msg.chat.id, "✅ Film muvaffaqiyatli saqlandi!")
    else:
        bot.send_message(msg.chat.id, "❌ Faqat MP4 video yuboring.")

@bot.message_handler(func=lambda m: m.text == "➕ Admin qo‘shish")
def add_admin(msg):
    if msg.from_user.id == OWNER_ID:
        bot.send_message(msg.chat.id, "Yangi admin ID sini kiriting:")
        bot.register_next_step_handler(msg, save_admin)

def save_admin(msg):
    try:
        admin_id = int(msg.text)
        cur.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))
        conn.commit()
        bot.send_message(msg.chat.id, "✅ Admin qo‘shildi.")
    except:
        bot.send_message(msg.chat.id, "❌ Noto‘g‘ri ID.")

@bot.message_handler(func=lambda m: m.text == "📺 Kanal sozlash")
def channel_settings(msg):
    if msg.from_user.id == OWNER_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Kanal qo‘shish", "➖ Kanal o‘chirish", "⬅️ Ortga")
        bot.send_message(msg.chat.id, "Kanal sozlamalari:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Kanal qo‘shish")
def add_channel(msg):
    if msg.from_user.id == OWNER_ID:
        bot.send_message(msg.chat.id, "Kanal username ni kiriting (@ bilan):")
        bot.register_next_step_handler(msg, save_channel)

def save_channel(msg):
    username = msg.text.strip()
    cur.execute("INSERT INTO channels (username) VALUES (?)", (username,))
    conn.commit()
    bot.send_message(msg.chat.id, f"✅ {username} kanal qo‘shildi.")

@bot.message_handler(func=lambda m: m.text == "➖ Kanal o‘chirish")
def delete_channel(msg):
    if msg.from_user.id == OWNER_ID:
        cur.execute("SELECT username FROM channels")
        chs = cur.fetchall()
        if not chs:
            bot.send_message(msg.chat.id, "❌ Hech qanday kanal yo‘q.")
            return
        markup = types.InlineKeyboardMarkup()
        for ch in chs:
            markup.add(types.InlineKeyboardButton(ch[0], callback_data=f"del_{ch[0]}"))
        bot.send_message(msg.chat.id, "O‘chirmoqchi bo‘lgan kanalni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def delete_channel_confirm(c):
    username = c.data[4:]
    cur.execute("DELETE FROM channels WHERE username=?", (username,))
    conn.commit()
    bot.answer_callback_query(c.id, "✅ O‘chirildi!")
    bot.delete_message(c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "📢 Reklama")
def broadcast(msg):
    if msg.from_user.id == OWNER_ID:
        bot.send_message(msg.chat.id, "Reklama xabarini yuboring:")
        bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(msg):
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    count = 0
    for u in users:
        try:
            bot.copy_message(u[0], msg.chat.id, msg.message_id)
            count += 1
        except:
            pass
    bot.send_message(msg.chat.id, f"✅ Reklama {count} foydalanuvchiga yuborildi.")

bot.polling(none_stop=True)
