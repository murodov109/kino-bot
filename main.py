import os, requests, json, asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
TMDB_KEY = "YOUR_TMDB_KEY"

if not os.path.exists("sub_channels.json"): json.dump([], open("sub_channels.json","w"))
if not os.path.exists("film_channels.json"): json.dump([], open("film_channels.json","w"))

def load_sub_channels(): return json.load(open("sub_channels.json"))
def save_sub_channels(lst): json.dump(lst, open("sub_channels.json","w"))
def load_film_channels(): return json.load(open("film_channels.json"))
def save_film_channels(lst): json.dump(lst, open("film_channels.json","w"))

app = Client("film-bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

def user_buttons():
    sub = load_sub_channels()
    buttons = [[InlineKeyboardButton(f"📌 {c} ▶", url=f"https://t.me/{c.replace('-100','')}")] for c in sub]
    buttons.append([InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)

def admin_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Film yuklash", callback_data="upload")],
        [InlineKeyboardButton("🎬 Film ma'lumotlari", callback_data="info")],
        [InlineKeyboardButton("⚙ Admin panel", callback_data="admin_panel")],
        [InlineKeyboardButton("⛔ Chiqish", callback_data="logout")]
    ])

def admin_panel_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Majburiy obuna kanal qo‘shish", callback_data="add_sub")],
        [InlineKeyboardButton("➖ Majburiy obuna kanal o‘chirish", callback_data="remove_sub")],
        [InlineKeyboardButton("📜 Majburiy obuna kanallari", callback_data="list_sub")],
        [InlineKeyboardButton("➕ Film qidirish kanal qo‘shish", callback_data="add_film")],
        [InlineKeyboardButton("➖ Film qidirish kanal o‘chirish", callback_data="remove_film")],
        [InlineKeyboardButton("📜 Film qidirish kanallari", callback_data="list_film")],
        [InlineKeyboardButton("⛔ Admin paneldan chiqish", callback_data="logout")]
    ])

async def find_video(client, title):
    res = []
    for ch in load_film_channels():
        async for msg in client.get_chat_history(ch, limit=3000):
            if msg.video and msg.caption and title.lower() in msg.caption.lower(): res.append(msg)
    return res

def search_tmdb(title):
    r = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={title}").json()
    return r["results"][0] if r.get("results") else None

@app.on_message(filters.private & filters.command("start"))
async def start(c,m):
    if m.from_user.id==ADMIN_ID:
        await m.reply("🛠 Admin panel", reply_markup=admin_buttons())
    else:
        await m.reply("🎬 Salom! Film nomini kiriting.", reply_markup=user_buttons())

@app.on_message(filters.private & filters.text)
async def user_panel(c,m):
    if m.from_user.id != ADMIN_ID:
        title = m.text.strip()
        sent = await m.reply("⏳ Qidirilyapti...")
        movie = search_tmdb(title)
        if movie:
            videos = await find_video(c, title)
            if videos:
                for v in videos: sent = await m.reply_video(v.video.file_id, caption=v.caption, reply_markup=user_buttons())
            else: await sent.edit_text("❌ Film kanalda topilmadi!")
        else: await sent.edit_text("❌ Film TMDB da topilmadi!")

@app.on_callback_query()
async def callback(c,q):
    sub = load_sub_channels()
    film = load_film_channels()
    data = q.data

    if data=="check_sub":
        ok = all((await c.get_chat_member(ch,q.from_user.id)).status!="left" for ch in sub)
        await q.answer("✅ Barcha kanallarga obuna bo‘ldingiz!" if ok else "❌ Iltimos barcha kanallarga obuna bo‘ling!")
    elif data=="admin_panel" and q.from_user.id==ADMIN_ID:
        await q.message.edit_text("⚙ Admin panel", reply_markup=admin_panel_buttons())
    elif data=="logout" and q.from_user.id==ADMIN_ID:
        await q.message.edit_text("Chiqdingiz", reply_markup=user_buttons())
    elif q.from_user.id==ADMIN_ID:
        if data=="list_sub": await q.answer("📜 "+", ".join(sub) if sub else "❌ Ro'yxat bo'sh")
        elif data=="list_film": await q.answer("📜 "+", ".join(film) if film else "❌ Ro'yxat bo'sh")
        elif data=="add_sub": sub.append("example_channel"); save_sub_channels(sub); await q.answer("➕ Kanal qo‘shildi")
        elif data=="remove_sub" and sub: sub.pop(); save_sub_channels(sub); await q.answer("➖ Kanal o‘chirildi")
        elif data=="add_film": film.append("example_film_channel"); save_film_channels(film); await q.answer("➕ Film kanali qo‘shildi")
        elif data=="remove_film" and film: film.pop(); save_film_channels(film); await q.answer("➖ Film kanali o‘chirildi")
        elif data in ["upload","info"]: await q.answer("ℹ️ Bu tugma hozir ishlamaydi!")

app.run()
