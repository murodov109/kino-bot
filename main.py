import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Client(
    "film_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    workers=4
)

mandatory_channels = []
film_channels = []
user_states = {}
total_users = set()
stats = {
    'daily_searches': 0,
    'total_searches': 0
}

def admin_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎬 Film kanallari"), KeyboardButton("📢 Majburiy obuna")],
        [KeyboardButton("📊 Statistika"), KeyboardButton("📣 Reklama tarqatish")],
        [KeyboardButton("👤 Foydalanuvchi rejimi")]
    ], resize_keyboard=True)

def user_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎬 Film qidirish")],
        [KeyboardButton("ℹ️ Bot haqida"), KeyboardButton("📞 Aloqa")]
    ], resize_keyboard=True)

def film_channel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="add_film")],
        [InlineKeyboardButton("➖ Kanal o'chirish", callback_data="del_film")],
        [InlineKeyboardButton("📋 Ro'yxatni ko'rish", callback_data="list_film")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]
    ])

def mandatory_channel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="add_mand")],
        [InlineKeyboardButton("➖ Kanal o'chirish", callback_data="del_mand")],
        [InlineKeyboardButton("📋 Ro'yxatni ko'rish", callback_data="list_mand")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]
    ])

def subscription_buttons():
    buttons = []
    for i, ch in enumerate(mandatory_channels, 1):
        ch_name = ch.replace("@", "")
        buttons.append([InlineKeyboardButton(f"📢 {i}-Kanal", url=f"https://t.me/{ch_name}")])
    buttons.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)

async def check_subscription(user_id):
    if not mandatory_channels:
        return True
    for ch in mandatory_channels:
        try:
            member = await app.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Obuna tekshirish xatosi {ch}: {e}")
            continue
    return True

async def search_films(query):
    results = []
    query_lower = query.lower()
    for channel in film_channels:
        try:
            count = 0
            async for message in app.get_chat_history(channel):
                if count >= 3000:
                    break
                if message.text and query_lower in message.text.lower():
                    results.append({
                        'channel': channel,
                        'message_id': message.id,
                        'text': message.text[:100]
                    })
                    if len(results) >= 20:
                        break
                count += 1
        except Exception as e:
            print(f"Qidiruv xatosi {channel}: {e}")
            continue
        if len(results) >= 20:
            break
    return results

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    total_users.add(user_id)
    
    try:
        if user_id == ADMIN_ID:
            await message.reply(
                f"👋 Assalomu alaykum, {username}!\n\n"
                "🎛 Admin paneliga xush kelibsiz.\n"
                "Kerakli bo'limni tanlang:",
                reply_markup=admin_menu()
            )
        else:
            if mandatory_channels and not await check_subscription(user_id):
                await message.reply(
                    f"👋 Salom, {username}!\n\n"
                    "🎬 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                    reply_markup=subscription_buttons()
                )
            else:
                await message.reply(
                    f"👋 Salom, {username}!\n\n"
                    "🎬 Film botiga xush kelibsiz!\n"
                    "Film qidirish uchun film nomini yozing yoki menyudan tanlang:",
                    reply_markup=user_menu()
                )
    except Exception as e:
        print(f"Start xatosi: {e}")

@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text
    
    try:
        if user_id == ADMIN_ID:
            if text == "🎬 Film kanallari":
                await message.reply(
                    "🎬 Film kanallari bo'limi\n\n"
                    "Bu yerda film qidirish uchun kanallarni boshqarishingiz mumkin:",
                    reply_markup=film_channel_menu()
                )
                return
            
            elif text == "📢 Majburiy obuna":
                await message.reply(
                    "📢 Majburiy obuna bo'limi\n\n"
                    "Bu yerda foydalanuvchilar obuna bo'lishi kerak bo'lgan kanallarni boshqarishingiz mumkin:",
                    reply_markup=mandatory_channel_menu()
                )
                return
            
            elif text == "📊 Statistika":
                await message.reply(
                    f"📊 **Bot statistikasi**\n\n"
                    f"👥 Jami foydalanuvchilar: {len(total_users)}\n"
                    f"🔍 Bugungi qidiruvlar: {stats['daily_searches']}\n"
                    f"📈 Jami qidiruvlar: {stats['total_searches']}\n"
                    f"🎬 Film kanallari: {len(film_channels)}\n"
                    f"📢 Majburiy kanallar: {len(mandatory_channels)}\n"
                    f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                return
            
            elif text == "📣 Reklama tarqatish":
                user_states[user_id] = "waiting_broadcast"
                await message.reply(
                    "📣 Reklama xabarini yuboring:\n\n"
                    "Xabar matn, rasm, video yoki gif bo'lishi mumkin.\n"
                    "Bekor qilish uchun /cancel yozing."
                )
                return
            
            elif text == "👤 Foydalanuvchi rejimi":
                await message.reply(
                    "👤 Foydalanuvchi rejimiga o'tdingiz:",
                    reply_markup=user_menu()
                )
                return
        
        if user_states.get(user_id) == "waiting_broadcast" and user_id == ADMIN_ID:
            await message.reply("⏳ Xabar barcha foydalanuvchilarga yuborilmoqda...")
            success = 0
            failed = 0
            for uid in total_users:
                try:
                    await client.copy_message(uid, message.chat.id, message.id)
                    success += 1
                    await asyncio.sleep(0.05)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except UserIsBlocked:
                    failed += 1
                except Exception:
                    failed += 1
            user_states.pop(user_id, None)
            await message.reply(
                f"✅ Reklama tarqatildi!\n\n"
                f"Muvaffaqiyatli: {success}\n"
                f"Xatolik: {failed}"
            )
            return
        
        if user_states.get(user_id) == "waiting_film_channel" and user_id == ADMIN_ID:
            channel = text.strip()
            if not channel.startswith("@"):
                channel = "@" + channel
            film_channels.append(channel)
            user_states.pop(user_id, None)
            await message.reply(
                f"✅ Kanal qo'shildi: {channel}\n\n"
                f"Jami film kanallari: {len(film_channels)}",
                reply_markup=film_channel_menu()
            )
            return
        
        if user_states.get(user_id) == "waiting_mand_channel" and user_id == ADMIN_ID:
            channel = text.strip()
            if not channel.startswith("@"):
                channel = "@" + channel
            mandatory_channels.append(channel)
            user_states.pop(user_id, None)
            await message.reply(
                f"✅ Kanal qo'shildi: {channel}\n\n"
                f"Jami majburiy kanallar: {len(mandatory_channels)}",
                reply_markup=mandatory_channel_menu()
            )
            return
        
        if text == "🎬 Film qidirish":
            await message.reply("🎬 Film nomini kiriting:")
            return
        
        if text == "ℹ️ Bot haqida":
            await message.reply(
                "ℹ️ **Bot haqida**\n\n"
                "Bu bot orqali siz kino va seriallarni tez va oson topishingiz mumkin.\n\n"
                "Faqat film nomini yozing va natijalarni oling!"
            )
            return
        
        if text == "📞 Aloqa":
            await message.reply("📞 **Aloqa**\n\nSavol va takliflar uchun: @admin")
            return
        
        if user_id != ADMIN_ID:
            if not await check_subscription(user_id):
                await message.reply(
                    "⚠️ Botdan foydalanish uchun kanallarga obuna bo'ling:",
                    reply_markup=subscription_buttons()
                )
                return
            
            stats['daily_searches'] += 1
            stats['total_searches'] += 1
            
            wait_msg = await message.reply("🔍 Qidirilmoqda...")
            results = await search_films(text)
            
            if results:
                buttons = []
                for i, result in enumerate(results[:15], 1):
                    ch_name = result['channel'].replace("@", "")
                    buttons.append([
                        InlineKeyboardButton(
                            f"🎬 Natija {i}",
                            url=f"https://t.me/{ch_name}/{result['message_id']}"
                        )
                    ])
                await wait_msg.edit_text(
                    f"✅ **{len(results)} ta natija topildi!**\n\n"
                    f"🔍 Qidiruv: {text}",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            else:
                await wait_msg.edit_text(
                    f"❌ **'{text}' bo'yicha natija topilmadi**\n\n"
                    "Boshqa nom bilan qidirib ko'ring."
                )
    except Exception as e:
        print(f"Text handler xatosi: {e}")

@app.on_callback_query()
async def callback_handler(client, callback):
    data = callback.data
    user_id = callback.from_user.id
    
    try:
        if data == "check_sub":
            if await check_subscription(user_id):
                await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
                await callback.message.delete()
                await client.send_message(
                    user_id,
                    f"👋 Salom, {callback.from_user.first_name}!\n\n"
                    "🎬 Film botiga xush kelibsiz!\n"
                    "Film qidirish uchun film nomini yozing:",
                    reply_markup=user_menu()
                )
            else:
                await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
            return
        
        if user_id != ADMIN_ID:
            await callback.answer("⛔ Bu admin funksiyasi", show_alert=True)
            return
        
        if data == "back_admin":
            await callback.message.delete()
            await client.send_message(
                user_id,
                "🎛 Admin paneliga xush kelibsiz.\nKerakli bo'limni tanlang:",
                reply_markup=admin_menu()
            )
        
        elif data == "add_film":
            user_states[user_id] = "waiting_film_channel"
            await callback.message.edit_text(
                "➕ **Film kanali qo'shish**\n\n"
                "Kanal username kiriting (masalan: @kanalnom):"
            )
        
        elif data == "del_film":
            if film_channels:
                removed = film_channels.pop()
                await callback.answer(f"✅ O'chirildi: {removed}", show_alert=True)
                await callback.message.edit_reply_markup(reply_markup=film_channel_menu())
            else:
                await callback.answer("❌ Ro'yxat bo'sh", show_alert=True)
        
        elif data == "list_film":
            if film_channels:
                text = "📋 **Film kanallari ro'yxati:**\n\n" + "\n".join(
                    f"{i}. {ch}" for i, ch in enumerate(film_channels, 1)
                )
            else:
                text = "📋 Film kanallari ro'yxati bo'sh"
            await callback.message.edit_text(text, reply_markup=film_channel_menu())
        
        elif data == "add_mand":
            user_states[user_id] = "waiting_mand_channel"
            await callback.message.edit_text(
                "➕ **Majburiy kanal qo'shish**\n\n"
                "Kanal username kiriting (masalan: @kanalnom):"
            )
        
        elif data == "del_mand":
            if mandatory_channels:
                removed = mandatory_channels.pop()
                await callback.answer(f"✅ O'chirildi: {removed}", show_alert=True)
                await callback.message.edit_reply_markup(reply_markup=mandatory_channel_menu())
            else:
                await callback.answer("❌ Ro'yxat bo'sh", show_alert=True)
        
        elif data == "list_mand":
            if mandatory_channels:
                text = "📋 **Majburiy kanallar ro'yxati:**\n\n" + "\n".join(
                    f"{i}. {ch}" for i, ch in enumerate(mandatory_channels, 1)
                )
            else:
                text = "📋 Majburiy kanallar ro'yxati bo'sh"
            await callback.message.edit_text(text, reply_markup=mandatory_channel_menu())
    
    except Exception as e:
        print(f"Callback xatosi: {e}")

if __name__ == "__main__":
    print("🚀 Bot ishga tushmoqda...")
    try:
        app.run()
    except Exception as e:
        print(f"Bot ishga tushirishda xato: {e}")
