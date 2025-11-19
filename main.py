import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Client("film_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

mandatory_channels = []
film_channels = []

async def check_subs(user_id):
    for ch in mandatory_channels:
        try:
            m = await app.get_chat_member(ch, user_id)
            if m.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

async def search_film(name):
    res = []
    for ch in film_channels:
        async for m in app.get_chat_history(ch, limit=3000):
            if m.text and name.lower() in m.text.lower():
                res.append((ch, m.message_id))
    return res

def user_panel():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_sub")]])

def admin_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Film yuklash", callback_data="upload")],
        [InlineKeyboardButton("🎬 Film qidirish", callback_data="search")],
        [InlineKeyboardButton("⚙️ Admin panel", callback_data="admin_inner")],
        [InlineKeyboardButton("⛔ Chiqish", callback_data="exit")]
    ])

def admin_inner_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Majburiy obuna qo‘shish", callback_data="add_mand")],
        [InlineKeyboardButton("➖ Majburiy obuna o‘chirish", callback_data="del_mand")],
        [InlineKeyboardButton("📜 Majburiy obuna ro‘yxati", callback_data="list_mand")],
        [InlineKeyboardButton("➕ Film kanal qo‘shish", callback_data="add_film")],
        [InlineKeyboardButton("➖ Film kanal o‘chirish", callback_data="del_film")],
        [InlineKeyboardButton("📜 Film kanallari ro‘yxati", callback_data="list_film")],
        [InlineKeyboardButton("⛔ Chiqish", callback_data="exit_inner")]
    ])

@app.on_message(filters.command(["start"]))
async def start(_, m):
    if m.from_user.id == ADMIN_ID:
        await m.reply("Admin panel", reply_markup=admin_panel())
    else:
        await m.reply("Film nomini yozing", reply_markup=user_panel())

@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(_, m):
    if m.from_user.id != ADMIN_ID and not await check_subs(m.from_user.id):
        await m.reply("Majburiy obuna bo‘ling", reply_markup=user_panel())
        return

    if m.from_user.id != ADMIN_ID:
        films = await search_film(m.text)
        if films:
            kb = [[InlineKeyboardButton(f"📌 {ch}", url=f"https://t.me/{ch}/{mid}")] for ch, mid in films]
            await m.reply("🎬 Topildi", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await m.reply("❌ Film topilmadi")

@app.on_callback_query()
async def cb(_, c):
    data = c.data
    u = c.from_user.id

    if data == "check_sub":
        if await check_subs(u):
            await c.answer("✅ Obuna tasdiqlandi", show_alert=True)
        else:
            await c.answer("❗ Majburiy obuna yo‘q", show_alert=True)
        return

    if u == ADMIN_ID:
        if data == "admin_inner":
            await c.message.edit("⚙️ Ichki admin panel", reply_markup=admin_inner_panel())
        elif data == "exit_inner":
            await c.message.edit("Admin panel", reply_markup=admin_panel())
        elif data == "list_mand":
            txt = "\n".join(mandatory_channels) if mandatory_channels else "Yo‘q"
            await c.message.edit(f"📜 Majburiy obuna:\n{txt}")
        elif data == "list_film":
            txt = "\n".join(film_channels) if film_channels else "Yo‘q"
            await c.message.edit(f"🎬 Film kanallari:\n{txt}")
        elif data == "add_mand":
            mandatory_channels.append("channel_username")
            await c.answer("➕ Qo‘shildi", show_alert=True)
        elif data == "del_mand":
            if mandatory_channels:
                mandatory_channels.pop()
            await c.answer("➖ O‘chirildi", show_alert=True)
        elif data == "add_film":
            film_channels.append("channel_username")
            await c.answer("➕ Qo‘shildi", show_alert=True)
        elif data == "del_film":
            if film_channels:
                film_channels.pop()
            await c.answer("➖ O‘chirildi", show_alert=True)

app.run()
