import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup
from pyrogram.errors import UserNotParticipant, FloodWait
from dotenv import load_dotenv
import asyncio

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
BOT_USERNAME = os.getenv("BOT_USERNAME", "bot_username")

app = Client("cinema_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

movies = {}
channels = []
stats = {"users": set(), "total_requests": 0}
upload_state = {}
main_admins = ADMIN_IDS.copy()

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_main_admin(user_id):
    return user_id in main_admins

def admin_panel_markup(user_id):
    keyboard = [
        ["📊 Statistika", "📢 Reklama tarqatish"],
        ["➕ Majburiy obuna", "➖ Obuna o'chirish"],
        ["🎬 Film qo'shish", "🗑 Film o'chirish"],
        ["📋 Kanallar ro'yxati"]
    ]
    if is_main_admin(user_id):
        keyboard.append(["👤 Admin qo'shish", "❌ Admin o'chirish"])
        keyboard.append(["📝 Adminlar ro'yxati"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def check_subscription(user_id):
    if not channels:
        return True
    for channel in channels:
        try:
            await app.get_chat_member(channel, user_id)
        except UserNotParticipant:
            return False
        except Exception:
            continue
    return True

def subscription_markup():
    buttons = []
    for i, channel in enumerate(channels):
        channel_clean = channel.replace("@", "")
        buttons.append([InlineKeyboardButton(f"📢 Kanal {i+1}", url=f"https://t.me/{channel_clean}")])
    buttons.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    stats["users"].add(user_id)
    
    if is_admin(user_id):
        await message.reply_text("🎬 Kino Bot Admin Panel", reply_markup=admin_panel_markup(user_id))
    else:
        if not await check_subscription(user_id):
            await message.reply_text("❌ Botdan foydalanish uchun kanallarga obuna bo'ling:", reply_markup=subscription_markup())
        else:
            await message.reply_text(f"🎬 Kino kodini yuboring\n\n🎥 Eng yangi premyeralar faqat bizda @{BOT_USERNAME}")

@app.on_message(filters.private & filters.text & ~filters.command("start"))
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    text = message.text
    
    if is_admin(user_id):
        if text == "📊 Statistika":
            msg = f"📊 **Bot Statistikasi**\n\n"
            msg += f"👥 Foydalanuvchilar: **{len(stats['users'])}**\n"
            msg += f"📊 So'rovlar: **{stats['total_requests']}**\n"
            msg += f"🎬 Filmlar: **{len(movies)}**\n"
            msg += f"📢 Kanallar: **{len(channels)}**"
            await message.reply_text(msg)
        
        elif text == "📢 Reklama tarqatish":
            upload_state[user_id] = "waiting_ad"
            await message.reply_text("📢 Reklama xabarini yuboring:")
        
        elif text == "➕ Majburiy obuna":
            upload_state[user_id] = "waiting_channel"
            await message.reply_text("📢 Kanal username yuboring (@channel):")
        
        elif text == "➖ Obuna o'chirish":
            if channels:
                msg = "📋 **Majburiy obuna kanallari:**\n\n"
                for i, ch in enumerate(channels):
                    msg += f"{i+1}. {ch}\n"
                msg += "\n🗑 O'chirish uchun raqamni yuboring:"
                await message.reply_text(msg)
                upload_state[user_id] = "delete_channel"
            else:
                await message.reply_text("❌ Kanallar yo'q")
        
        elif text == "🎬 Film qo'shish":
            upload_state[user_id] = "waiting_video"
            await message.reply_text("🎥 Film videosini yuboring:")
        
        elif text == "🗑 Film o'chirish":
            if movies:
                msg = "🎬 **Filmlar ro'yxati:**\n\n"
                for code, data in movies.items():
                    msg += f"📝 Kod: `{code}`\n🎬 Nom: {data['name']}\n\n"
                msg += "🗑 O'chirish uchun kodni yuboring:"
                await message.reply_text(msg)
                upload_state[user_id] = "delete_movie"
            else:
                await message.reply_text("❌ Filmlar yo'q")
        
        elif text == "📋 Kanallar ro'yxati":
            if channels:
                msg = "📋 **Majburiy obuna kanallari:**\n\n"
                for i, ch in enumerate(channels):
                    msg += f"{i+1}. {ch}\n"
                await message.reply_text(msg)
            else:
                await message.reply_text("❌ Kanallar yo'q")
        
        elif text == "👤 Admin qo'shish" and is_main_admin(user_id):
            upload_state[user_id] = "waiting_admin"
            await message.reply_text("👤 Admin ID raqamini yuboring:")
        
        elif text == "❌ Admin o'chirish" and is_main_admin(user_id):
            if len(ADMIN_IDS) > len(main_admins):
                msg = "📋 **Adminlar ro'yxati:**\n\n"
                for admin_id in ADMIN_IDS:
                    if admin_id not in main_admins:
                        msg += f"🆔 `{admin_id}`\n"
                msg += "\n❌ O'chirish uchun ID raqamini yuboring:"
                await message.reply_text(msg)
                upload_state[user_id] = "delete_admin"
            else:
                await message.reply_text("❌ O'chiriladigan adminlar yo'q")
        
        elif text == "📝 Adminlar ro'yxati" and is_main_admin(user_id):
            msg = "📋 **Barcha adminlar:**\n\n"
            for i, admin_id in enumerate(ADMIN_IDS):
                status = "👑 Asosiy" if admin_id in main_admins else "👤 Oddiy"
                msg += f"{i+1}. {status} - `{admin_id}`\n"
            await message.reply_text(msg)
        
        elif user_id in upload_state:
            state = upload_state[user_id]
            
            if state == "waiting_ad":
                success = 0
                for uid in stats["users"]:
                    try:
                        await client.send_message(uid, text)
                        success += 1
                        await asyncio.sleep(0.05)
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except Exception:
                        pass
                await message.reply_text(f"✅ Reklama {success} ta foydalanuvchiga yuborildi")
                del upload_state[user_id]
            
            elif state == "waiting_channel":
                if text.startswith("@"):
                    channels.append(text)
                    await message.reply_text(f"✅ Kanal qo'shildi: {text}")
                else:
                    await message.reply_text("❌ @ bilan boshlanadigan kanal nomini yuboring")
                del upload_state[user_id]
            
            elif state == "delete_channel":
                try:
                    idx = int(text) - 1
                    if 0 <= idx < len(channels):
                        ch = channels.pop(idx)
                        await message.reply_text(f"✅ O'chirildi: {ch}")
                    else:
                        await message.reply_text("❌ Noto'g'ri raqam")
                except ValueError:
                    await message.reply_text("❌ Faqat raqam yuboring")
                del upload_state[user_id]
            
            elif isinstance(state, dict) and state.get("state") == "waiting_name":
                upload_state[user_id]["name"] = text
                upload_state[user_id]["state"] = "waiting_code"
                await message.reply_text("🔢 Film kodini yuboring:")
            
            elif isinstance(state, dict) and state.get("state") == "waiting_code":
                code = text.strip()
                video_data = upload_state[user_id]
                movies[code] = {
                    "video_id": video_data["video"]["id"],
                    "name": video_data["name"],
                    "duration": video_data["video"]["duration"],
                    "size": video_data["video"]["size"]
                }
                
                duration_min = video_data["video"]["duration"] // 60
                size_mb = video_data["video"]["size"] / (1024 * 1024)
                
                confirm_msg = f"✅ **Film tasdiqlandi**\n\n"
                confirm_msg += f"🎬 Nomi: **{video_data['name']}**\n"
                confirm_msg += f"🔢 Kodi: `{code}`\n"
                confirm_msg += f"⏱ Davomiylik: **{duration_min} daqiqa**\n"
                confirm_msg += f"📦 Hajmi: **{size_mb:.1f} MB**"
                
                await message.reply_text(confirm_msg)
                del upload_state[user_id]
            
            elif state == "delete_movie":
                if text in movies:
                    movie_name = movies[text]["name"]
                    del movies[text]
                    await message.reply_text(f"✅ Film o'chirildi: **{movie_name}**")
                else:
                    await message.reply_text("❌ Film topilmadi")
                del upload_state[user_id]
            
            elif state == "waiting_admin" and is_main_admin(user_id):
                try:
                    new_admin = int(text)
                    if new_admin not in ADMIN_IDS:
                        ADMIN_IDS.append(new_admin)
                        await message.reply_text(f"✅ Admin qo'shildi: `{new_admin}`")
                    else:
                        await message.reply_text("❌ Bu ID allaqachon admin")
                except ValueError:
                    await message.reply_text("❌ Noto'g'ri ID raqam")
                del upload_state[user_id]
            
            elif state == "delete_admin" and is_main_admin(user_id):
                try:
                    del_admin = int(text)
                    if del_admin in main_admins:
                        await message.reply_text("❌ Asosiy adminni o'chirib bo'lmaydi")
                    elif del_admin in ADMIN_IDS:
                        ADMIN_IDS.remove(del_admin)
                        await message.reply_text(f"✅ Admin o'chirildi: `{del_admin}`")
                    else:
                        await message.reply_text("❌ Admin topilmadi")
                except ValueError:
                    await message.reply_text("❌ Noto'g'ri ID raqam")
                del upload_state[user_id]
    else:
        if not await check_subscription(user_id):
            await message.reply_text("❌ Avval kanallarga obuna bo'ling:", reply_markup=subscription_markup())
            return
        
        code = text.strip()
        if code in movies:
            stats["total_requests"] += 1
            movie = movies[code]
            duration_min = movie['duration'] // 60
            size_mb = movie['size'] / (1024 * 1024)
            
            caption = f"🎬 **{movie['name']}**\n\n"
            caption += f"🔢 Kod: `{code}`\n"
            caption += f"⏱ Davomiylik: **{duration_min} daqiqa**\n"
            caption += f"📦 Hajmi: **{size_mb:.1f} MB**\n\n"
            caption += f"🎥 Eng yangi premyeralar faqat bizda @{BOT_USERNAME}"
            
            try:
                await client.send_video(user_id, movie["video_id"], caption=caption)
            except Exception:
                await message.reply_text("❌ Xatolik yuz berdi, qayta urinib ko'ring")
        else:
            await message.reply_text(f"❌ Film topilmadi\n\n🔍 To'g'ri kodni kiriting\n\n🎥 Eng yangi premyeralar faqat bizda @{BOT_USERNAME}")

@app.on_message(filters.private & filters.video)
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id) and user_id in upload_state and upload_state[user_id] == "waiting_video":
        duration = message.video.duration
        size = message.video.file_size
        duration_min = duration // 60
        size_mb = size / (1024 * 1024)
        
        upload_state[user_id] = {
            "state": "waiting_name",
            "video": {
                "id": message.video.file_id,
                "duration": duration,
                "size": size
            }
        }
        
        info_msg = f"✅ **Video qabul qilindi**\n\n"
        info_msg += f"⏱ Davomiylik: **{duration_min} daqiqa**\n"
        info_msg += f"📦 Hajmi: **{size_mb:.1f} MB**\n\n"
        info_msg += f"📝 Film nomini yuboring:"
        
        await message.reply_text(info_msg)

@app.on_message(filters.private & ~filters.video & ~filters.text)
async def handle_other_media(client, message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id) and user_id in upload_state and upload_state[user_id] == "waiting_video":
        await message.reply_text("❌ Faqat video yuboring!\n\n🎥 Film videosini yuboring:")

@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if await check_subscription(user_id):
        await callback_query.message.delete()
        await client.send_message(user_id, f"✅ **Obuna tasdiqlandi!**\n\n🎬 Kino kodini yuboring\n\n🎥 Eng yangi premyeralar faqat bizda @{BOT_USERNAME}")
    else:
        await callback_query.answer("❌ Barcha kanallarga obuna bo'ling!", show_alert=True)

print("🚀 Bot ishga tushdi...")
app.run()
