import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, ChatAdminRequired

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

def back_button():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔙 Orqaga")]
    ], resize_keyboard=True)

def subscription_buttons():
    buttons = []
    for i, ch in enumerate(mandatory_channels, 1):
        ch_name = ch.replace("@", "").replace("https://t.me/", "")
        buttons.append([InlineKeyboardButton(f"📢 {i}-Kanal", url=f"https://t.me/{ch_name}")])
    buttons.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)

async def is_user_member(user_id, channel):
    try:
        member = await app.get_chat_member(channel, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        print(f"Obuna tekshirish xatosi {channel}: {e}")
        return False

async def check_all_subscriptions(user_id):
    if not mandatory_channels:
        return True
    
    for channel in mandatory_channels:
        is_member = await is_user_member(user_id, channel)
        if not is_member:
            return False
    return True

async def search_films(query):
    results = []
    query_lower = query.lower().strip()
    
    if not film_channels:
        return results
    
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
                        return results
                count += 1
        except Exception as e:
            print(f"Qidiruv xatosi {channel}: {e}")
            continue
    
    return results

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    total_users.add(user_id)
    
    try:
        if user_id == ADMIN_ID:
            await message.reply(
                f"👋 Assalomu alaykum, {username}!\n\n"
                "🎛 **Admin paneliga xush kelibsiz**\n\n"
                "Kerakli bo'limni tanlang:",
                reply_markup=admin_menu()
            )
        else:
            if mandatory_channels:
                is_subscribed = await check_all_subscriptions(user_id)
                if not is_subscribed:
                    await message.reply(
                        f"👋 Salom, **{username}**!\n\n"
                        "🎬 **Film botiga xush kelibsiz!**\n\n"
                        "⚠️ Botdan foydalanish uchun quyidagi **barcha kanallarga** obuna bo'ling:\n\n"
                        "👇 Kanallarga obuna bo'lib, keyin **✅ Obunani tekshirish** tugmasini bosing:",
                        reply_markup=subscription_buttons()
                    )
                    return
            
            await message.reply(
                f"👋 Salom, **{username}**!\n\n"
                "🎬 **Film botiga xush kelibsiz!**\n\n"
                "Film qidirish uchun film nomini yozing yoki menyudan tanlang:",
                reply_markup=user_menu()
            )
    except Exception as e:
        print(f"Start xatosi: {e}")

@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def text_message_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    try:
        if user_id == ADMIN_ID:
            if text == "🎬 Film kanallari":
                await message.reply(
                    "🎬 **Film kanallari boshqaruvi**\n\n"
                    "Quyidagi buyruqlardan birini tanlang:\n\n"
                    "➕ Kanal qo'shish\n"
                    "➖ Kanal o'chirish\n"
                    "📋 Ro'yxatni ko'rish\n"
                    "🔙 Orqaga",
                    reply_markup=back_button()
                )
                user_states[user_id] = "film_menu"
                return
            
            elif text == "📢 Majburiy obuna":
                await message.reply(
                    "📢 **Majburiy obuna boshqaruvi**\n\n"
                    "Quyidagi buyruqlardan birini tanlang:\n\n"
                    "➕ Kanal qo'shish\n"
                    "➖ Kanal o'chirish\n"
                    "📋 Ro'yxatni ko'rish\n"
                    "🔙 Orqaga",
                    reply_markup=back_button()
                )
                user_states[user_id] = "mandatory_menu"
                return
            
            elif text == "📊 Statistika":
                await message.reply(
                    f"📊 **Bot statistikasi**\n\n"
                    f"👥 Jami foydalanuvchilar: **{len(total_users)}**\n"
                    f"🔍 Bugungi qidiruvlar: **{stats['daily_searches']}**\n"
                    f"📈 Jami qidiruvlar: **{stats['total_searches']}**\n"
                    f"🎬 Film kanallari: **{len(film_channels)}**\n"
                    f"📢 Majburiy kanallar: **{len(mandatory_channels)}**\n"
                    f"📅 Sana: **{datetime.now().strftime('%Y-%m-%d %H:%M')}**"
                )
                return
            
            elif text == "📣 Reklama tarqatish":
                user_states[user_id] = "waiting_broadcast"
                await message.reply(
                    "📣 **Reklama xabarini yuboring:**\n\n"
                    "Xabar matn, rasm, video yoki gif bo'lishi mumkin.\n\n"
                    "Bekor qilish uchun /cancel yozing.",
                    reply_markup=back_button()
                )
                return
            
            elif text == "👤 Foydalanuvchi rejimi":
                user_states.pop(user_id, None)
                await message.reply(
                    "👤 **Foydalanuvchi rejimiga o'tdingiz**\n\n"
                    "Film qidirish uchun film nomini yozing:",
                    reply_markup=user_menu()
                )
                return
            
            elif text == "🔙 Orqaga":
                user_states.pop(user_id, None)
                await message.reply(
                    "🎛 **Admin panel**\n\n"
                    "Kerakli bo'limni tanlang:",
                    reply_markup=admin_menu()
                )
                return
            
            if user_states.get(user_id) == "film_menu":
                if text == "➕ Kanal qo'shish":
                    user_states[user_id] = "adding_film_channel"
                    await message.reply(
                        "➕ **Film kanali qo'shish**\n\n"
                        "Kanal username yoki linkini yuboring:\n\n"
                        "Masalan: @kanalnom\n"
                        "yoki: https://t.me/kanalnom",
                        reply_markup=back_button()
                    )
                    return
                
                elif text == "➖ Kanal o'chirish":
                    if film_channels:
                        channel_list = "\n".join([f"{i}. {ch}" for i, ch in enumerate(film_channels, 1)])
                        user_states[user_id] = "deleting_film_channel"
                        await message.reply(
                            f"➖ **Film kanali o'chirish**\n\n"
                            f"📋 Mavjud kanallar:\n{channel_list}\n\n"
                            f"O'chirmoqchi bo'lgan kanal raqamini yuboring:",
                            reply_markup=back_button()
                        )
                    else:
                        await message.reply("❌ Film kanallari ro'yxati bo'sh")
                    return
                
                elif text == "📋 Ro'yxatni ko'rish":
                    if film_channels:
                        channel_list = "\n".join([f"{i}. {ch}" for i, ch in enumerate(film_channels, 1)])
                        await message.reply(
                            f"📋 **Film kanallari ro'yxati:**\n\n{channel_list}\n\n"
                            f"Jami: **{len(film_channels)}** ta kanal"
                        )
                    else:
                        await message.reply("📋 Film kanallari ro'yxati bo'sh")
                    return
            
            if user_states.get(user_id) == "mandatory_menu":
                if text == "➕ Kanal qo'shish":
                    user_states[user_id] = "adding_mandatory_channel"
                    await message.reply(
                        "➕ **Majburiy kanal qo'shish**\n\n"
                        "Kanal username yoki linkini yuboring:\n\n"
                        "Masalan: @kanalnom\n"
                        "yoki: https://t.me/kanalnom",
                        reply_markup=back_button()
                    )
                    return
                
                elif text == "➖ Kanal o'chirish":
                    if mandatory_channels:
                        channel_list = "\n".join([f"{i}. {ch}" for i, ch in enumerate(mandatory_channels, 1)])
                        user_states[user_id] = "deleting_mandatory_channel"
                        await message.reply(
                            f"➖ **Majburiy kanal o'chirish**\n\n"
                            f"📋 Mavjud kanallar:\n{channel_list}\n\n"
                            f"O'chirmoqchi bo'lgan kanal raqamini yuboring:",
                            reply_markup=back_button()
                        )
                    else:
                        await message.reply("❌ Majburiy kanallar ro'yxati bo'sh")
                    return
                
                elif text == "📋 Ro'yxatni ko'rish":
                    if mandatory_channels:
                        channel_list = "\n".join([f"{i}. {ch}" for i, ch in enumerate(mandatory_channels, 1)])
                        await message.reply(
                            f"📋 **Majburiy kanallar ro'yxati:**\n\n{channel_list}\n\n"
                            f"Jami: **{len(mandatory_channels)}** ta kanal"
                        )
                    else:
                        await message.reply("📋 Majburiy kanallar ro'yxati bo'sh")
                    return
            
            if user_states.get(user_id) == "adding_film_channel":
                channel = text.replace("https://t.me/", "@").strip()
                if not channel.startswith("@"):
                    channel = "@" + channel
                
                if channel in film_channels:
                    await message.reply("⚠️ Bu kanal allaqachon ro'yxatda mavjud!")
                else:
                    film_channels.append(channel)
                    user_states[user_id] = "film_menu"
                    await message.reply(
                        f"✅ **Kanal muvaffaqiyatli qo'shildi!**\n\n"
                        f"📢 Kanal: {channel}\n"
                        f"📊 Jami film kanallari: **{len(film_channels)}**",
                        reply_markup=back_button()
                    )
                return
            
            if user_states.get(user_id) == "adding_mandatory_channel":
                channel = text.replace("https://t.me/", "@").strip()
                if not channel.startswith("@"):
                    channel = "@" + channel
                
                if channel in mandatory_channels:
                    await message.reply("⚠️ Bu kanal allaqachon ro'yxatda mavjud!")
                else:
                    mandatory_channels.append(channel)
                    user_states[user_id] = "mandatory_menu"
                    await message.reply(
                        f"✅ **Kanal muvaffaqiyatli qo'shildi!**\n\n"
                        f"📢 Kanal: {channel}\n"
                        f"📊 Jami majburiy kanallar: **{len(mandatory_channels)}**",
                        reply_markup=back_button()
                    )
                return
            
            if user_states.get(user_id) == "deleting_film_channel":
                if text.isdigit():
                    index = int(text) - 1
                    if 0 <= index < len(film_channels):
                        removed = film_channels.pop(index)
                        user_states[user_id] = "film_menu"
                        await message.reply(
                            f"✅ **Kanal muvaffaqiyatli o'chirildi!**\n\n"
                            f"📢 O'chirilgan kanal: {removed}\n"
                            f"📊 Qolgan kanallar: **{len(film_channels)}**",
                            reply_markup=back_button()
                        )
                    else:
                        await message.reply("❌ Noto'g'ri raqam. Iltimos, ro'yxatdagi raqamni kiriting.")
                else:
                    await message.reply("❌ Iltimos, faqat raqam kiriting.")
                return
            
            if user_states.get(user_id) == "deleting_mandatory_channel":
                if text.isdigit():
                    index = int(text) - 1
                    if 0 <= index < len(mandatory_channels):
                        removed = mandatory_channels.pop(index)
                        user_states[user_id] = "mandatory_menu"
                        await message.reply(
                            f"✅ **Kanal muvaffaqiyatli o'chirildi!**\n\n"
                            f"📢 O'chirilgan kanal: {removed}\n"
                            f"📊 Qolgan kanallar: **{len(mandatory_channels)}**",
                            reply_markup=back_button()
                        )
                    else:
                        await message.reply("❌ Noto'g'ri raqam. Iltimos, ro'yxatdagi raqamni kiriting.")
                else:
                    await message.reply("❌ Iltimos, faqat raqam kiriting.")
                return
            
            if user_states.get(user_id) == "waiting_broadcast":
                await message.reply("⏳ **Xabar barcha foydalanuvchilarga yuborilmoqda...**")
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
                    f"✅ **Reklama muvaffaqiyatli tarqatildi!**\n\n"
                    f"📊 Muvaffaqiyatli: **{success}**\n"
                    f"❌ Xatolik: **{failed}**",
                    reply_markup=admin_menu()
                )
                return
        
        if text == "🎬 Film qidirish":
            await message.reply(
                "🎬 **Film qidirish**\n\n"
                "Film nomini kiriting:"
            )
            return
        
        if text == "ℹ️ Bot haqida":
            await message.reply(
                "ℹ️ **Bot haqida**\n\n"
                "🎬 Bu bot orqali siz kino va seriallarni tez va oson topishingiz mumkin.\n\n"
                "✨ Faqat film nomini yozing va natijalarni oling!\n\n"
                "🚀 Bot doimo yangilanib turadi."
            )
            return
        
        if text == "📞 Aloqa":
            await message.reply(
                "📞 **Aloqa**\n\n"
                "📧 Savol va takliflar uchun: @admin\n\n"
                "💬 Sizning fikr va mulohazalaringiz biz uchun muhim!"
            )
            return
        
        if user_id != ADMIN_ID:
            if mandatory_channels:
                is_subscribed = await check_all_subscriptions(user_id)
                if not is_subscribed:
                    await message.reply(
                        "⚠️ **Botdan foydalanish uchun barcha kanallarga obuna bo'ling!**\n\n"
                        "Kanallarga obuna bo'lib, keyin obunani tekshiring:",
                        reply_markup=subscription_buttons()
                    )
                    return
            
            stats['daily_searches'] += 1
            stats['total_searches'] += 1
            
            wait_msg = await message.reply("🔍 **Qidirilmoqda...**")
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
                    f"🔍 Qidiruv: **{text}**\n\n"
                    f"👇 Quyidagi tugmalardan kerakli filmni tanlang:",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            else:
                await wait_msg.edit_text(
                    f"❌ **'{text}' bo'yicha natija topilmadi**\n\n"
                    "💡 Boshqa nom bilan qidirib ko'ring yoki film nomini to'liq kiriting."
                )
    
    except Exception as e:
        print(f"Text handler xatosi: {e}")

@app.on_callback_query()
async def callback_query_handler(client, callback):
    user_id = callback.from_user.id
    data = callback.data
    
    try:
        if data == "check_sub":
            if mandatory_channels:
                is_subscribed = await check_all_subscriptions(user_id)
                if is_subscribed:
                    await callback.answer("✅ Obuna muvaffaqiyatli tasdiqlandi!", show_alert=True)
                    await callback.message.delete()
                    await client.send_message(
                        user_id,
                        f"🎉 **Tabriklaymiz!**\n\n"
                        f"✅ Siz barcha kanallarga obuna bo'ldingiz.\n\n"
                        f"🎬 Endi film qidirish uchun film nomini yozing:",
                        reply_markup=user_menu()
                    )
                else:
                    await callback.answer(
                        "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!\n\n"
                        "Iltimos, barcha kanallarga obuna bo'ling va qaytadan tekshiring.",
                        show_alert=True
                    )
            else:
                await callback.answer("✅ Obuna talab qilinmaydi!", show_alert=True)
    
    except Exception as e:
        print(f"Callback xatosi: {e}")
        await callback.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.", show_alert=True)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Film Bot ishga tushmoqda...")
    print("=" * 50)
    try:
        app.run()
    except Exception as e:
        print(f"❌ Bot ishga tushirishda xatolik: {e}")
