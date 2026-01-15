import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    BotCommand
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler
)
from datetime import datetime, timedelta

# 🔐 Admin Telegram ID
ADMIN_ID = 6659797188  # Faqat birinchi raqam qoldirildi

# 📢 Majburiy obuna kanallari
REQUIRED_CHANNELS = [
    {"name": "1 - Kanal", "username": "@kino_flash1", "url": "https://t.me/kino_flash1"}
]

# Kino qo'shish va o'chirish bosqichlari
KINO_ID, VIDEO, NOMI = range(3)
# Reklama bosqichi
REKLAMA = 4

# Admin menyusi
admin_menu = ReplyKeyboardMarkup([
    ['🎬 Kinolar', '📊 Statistika'],
    ['➕ Qo\'sh', '🗑 O\'chirish'],
    ['📢 Reklama', '❌ Menyu yopish']
], resize_keyboard=True)

# Foydalanuvchi menyusi (obuna bo'lgandan keyin)
user_menu = ReplyKeyboardMarkup([
    ['🎬 Kinolar ro\'yxati', '📋 Qanday ishlatish?'],
    ['📢 Reklama berish']
], resize_keyboard=True)


# SQLite baza yaratish
def baza_yarat():
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kinolar (
            id INTEGER PRIMARY KEY,
            file_id TEXT,
            nomi TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS foydalanuvchilar (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    con.commit()
    con.close()


# Foydalanuvchi barcha kanallarga obuna bo'lganligini tekshirish
def check_subscription(user_id, context):
    for channel in REQUIRED_CHANNELS:
        try:
            member = context.bot.get_chat_member(chat_id=channel["username"], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Xato: {e}")
            return False
    return True


# Kanal menyusini ko'rsatish
def show_channels_menu(update: Update, context: CallbackContext):
    buttons = []
    for channel in REQUIRED_CHANNELS:
        buttons.append([InlineKeyboardButton(channel['name'], url=channel['url'])])

    buttons.append([InlineKeyboardButton("✅ Obuna bo'ldim", callback_data='check_subs')])

    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text(
        "⚠️ Quyidagi 1-ta kanalga obuna bo'ling!",
        reply_markup=reply_markup
    )


# /start buyrug'i
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    # Foydalanuvchini bazaga qo'shish
    foydalanuvchi_qosh(user_id, user.username, user.first_name, user.last_name)

    # Admin uchun
    if user_id == ADMIN_ID:
        update.message.reply_text("🎥 Xush kelibsiz, admin!", reply_markup=admin_menu)
        return

    # Oddiy foydalanuvchilar uchun obuna tekshirish
    if not check_subscription(user_id, context):
        show_channels_menu(update, context)
        return

    update.message.reply_text(
        "🎬 Xush kelibsiz!\n\n"
        "📥 Kino ko'rish uchun kino ID raqamini yuboring yoki quyidagi menyulardan foydalaning.",
        reply_markup=user_menu
    )


# Foydalanuvchini bazaga qo'shish
def foydalanuvchi_qosh(user_id: int, username: str, first_name: str, last_name: str):
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT OR IGNORE INTO foydalanuvchilar (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        con.commit()
    except Exception as e:
        print(f"Foydalanuvchi qo'shishda xato: {e}")
    finally:
        con.close()


# Barcha foydalanuvchilarni olish
def barcha_foydalanuvchilarni_ol():
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    cur.execute("SELECT user_id FROM foydalanuvchilar")
    users = [row[0] for row in cur.fetchall()]
    con.close()
    return users


# Statistika ko'rsatish (faqat admin uchun)
def statistika(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()

    # Kinolar soni
    cur.execute("SELECT COUNT(*) FROM kinolar")
    kinolar_soni = cur.fetchone()[0]

    # Jami foydalanuvchilar
    cur.execute("SELECT COUNT(*) FROM foydalanuvchilar")
    jami_foydalanuvchilar = cur.fetchone()[0]

    # 1 kunlik foydalanuvchilar
    bir_kun_oldin = datetime.now() - timedelta(days=1)
    cur.execute("SELECT COUNT(*) FROM foydalanuvchilar WHERE joined_date > ?", (bir_kun_oldin,))
    kunlik_foydalanuvchilar = cur.fetchone()[0]

    # 1 haftalik foydalanuvchilar
    bir_hafta_oldin = datetime.now() - timedelta(weeks=1)
    cur.execute("SELECT COUNT(*) FROM foydalanuvchilar WHERE joined_date > ?", (bir_hafta_oldin,))
    haftalik_foydalanuvchilar = cur.fetchone()[0]

    # 1 oylik foydalanuvchilar
    bir_oy_oldin = datetime.now() - timedelta(days=30)
    cur.execute("SELECT COUNT(*) FROM foydalanuvchilar WHERE joined_date > ?", (bir_oy_oldin,))
    oylik_foydalanuvchilar = cur.fetchone()[0]

    con.close()

    update.message.reply_text(
        f"📊 Bot statistikasi:\n\n"
        f"🎬 Kinolar soni: {kinolar_soni}\n"
        f"👥 Jami foydalanuvchilar: {jami_foydalanuvchilar}\n"
        f"📈 1 kunlik: {kunlik_foydalanuvchilar}\n"
        f"📈 1 haftalik: {haftalik_foydalanuvchilar}\n"
        f"📈 1 oylik: {oylik_foydalanuvchilar}",
        reply_markup=admin_menu
    )


# Reklama yuborishni boshlash (admin uchun)
def reklama_boshlash(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    update.message.reply_text(
        "📢 Reklama yuborish uchun xabarni yuboring.\n\n"
        "📝 Xabar matn, rasm, video yoki boshqa formatda bo'lishi mumkin.\n"
        "❌ Bekor qilish uchun /cancel buyrug'ini yuboring.",
        reply_markup=ReplyKeyboardRemove()
    )
    return REKLAMA


# Reklama yuborish
def reklama_yuborish(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    # Foydalanuvchilar ro'yxatini olish
    users = barcha_foydalanuvchilarni_ol()
    total_users = len(users)
    successful = 0
    failed = 0

    update.message.reply_text(f"📤 Reklama {total_users} ta foydalanuvchiga yuborilmoqda...")

    # Xabarni barcha foydalanuvchilarga yuborish
    for user_id in users:
        try:
            # Original xabarni qayta yuborish
            if update.message.text:
                context.bot.send_message(chat_id=user_id, text=update.message.text)
            elif update.message.photo:
                context.bot.send_photo(chat_id=user_id, photo=update.message.photo[-1].file_id,
                                       caption=update.message.caption)
            elif update.message.video:
                context.bot.send_video(chat_id=user_id, video=update.message.video.file_id,
                                       caption=update.message.caption)
            elif update.message.document:
                context.bot.send_document(chat_id=user_id, document=update.message.document.file_id,
                                          caption=update.message.caption)
            else:
                context.bot.copy_message(chat_id=user_id, from_chat_id=update.message.chat_id,
                                         message_id=update.message.message_id)
            successful += 1
        except Exception as e:
            print(f"Xato: {e} - User ID: {user_id}")
            failed += 1


    update.message.reply_text(
        f"✅ Reklama yuborish yakunlandi!\n\n"
        f"📊 Natijalar:\n"
        f"• Jami: {total_users} ta\n"
        f"• Muvaffaqiyatli: {successful} ta\n"
        f"• Muvaffaqiyatsiz: {failed} ta",
        reply_markup=admin_menu
    )
    return ConversationHandler.END


def reklama_bekor(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    update.message.reply_text("X Reklama yuborish bekor qilindi.", reply_markup=admin_menu)
    return ConversationHandler.END


# Foydalanuvchi uchun reklama berish
def reklama_berish(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Obuna tekshirish
    if user_id != ADMIN_ID and not check_subscription(user_id, context):
        show_channels_menu(update, context)
        return

    update.message.reply_text(
        f"📢 Reklama joylashtirish uchun admin bilan bog'laning:\n\n"
        f"👤 Admin: @xoji_4\n"
        f"📞 Telegram: https://t.me/@xoji_4\n\n"
        f"💬 Taklif va reklamalar uchun xabaringizni qoldiring.",
        reply_markup=user_menu
    )


# Obunani tekshirish
def check_subscription_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if check_subscription(query.from_user.id, context):
        query.edit_message_text(
            "✅ Siz barcha kanallarga obuna bo'lgansiz!\n\n"
            "🎬 Xush kelibsiz! Endi botdan to'liq foydalanishingiz mumkin.\n"
            "📥 Kino ko'rish uchun kino ID raqamini yuboring yoki quyidagi menyulardan foydalaning."
        )
        # Foydalanuvchi menyusini yuborish
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Quyidagi menyulardan foydalaning:",
            reply_markup=user_menu
        )
    else:
        query.edit_message_text(
            "❌ Hali barcha kanallarga obuna bo'lmagansiz!\n\n"
            "Iltimos, quyidagi kanallarga obuna bo'ling:"
        )
        show_channels_menu_from_callback(query, context)


# Kanal menyusini callback uchun ko'rsatish
def show_channels_menu_from_callback(query, context):
    buttons = []
    for channel in REQUIRED_CHANNELS:
        buttons.append([InlineKeyboardButton(channel['name'], url=channel['url'])])

    buttons.append([InlineKeyboardButton("✅ Obuna bo'ldim", callback_data='check_subs')])

    reply_markup = InlineKeyboardMarkup(buttons)
    query.message.reply_text(
        "⚠️ Quyidagi 1-ta kanalga obuna bo'ling!",
        reply_markup=reply_markup
    )


# Kinolar ro'yxatini ko'rsatish
def kinolar_royxati(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Obuna tekshirish
    if user_id != ADMIN_ID and not check_subscription(user_id, context):
        show_channels_menu(update, context)
        return

    update.message.reply_text(
        f"🎬 Kinolar ro'yxati {REQUIRED_CHANNELS[0]['username']} kanalida mavjud!\n\n"
        f"Yoki botga kino ID raqamini yuboring.",
        reply_markup=user_menu
    )


# Qanday ishlatish bo'limi
def qanday_ishlatish(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID and not check_subscription(user_id, context):
        show_channels_menu(update, context)
        return

    update.message.reply_text(
        "📋 Botdan foydalanish qo'llanmasi:\n\n"
        "1. Kino ko'rish uchun faqat ID raqamini yuboring (masalan: 123)\n"
        "2. Kino topish uchun kanalda qidiring\n\n"
        "📝 Eslatma: Har bir kino uchun alohida ID raqami mavjud.",
        reply_markup=user_menu
    )


# ➕ Kino qo'shishni boshlash
def add_kino(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    update.message.reply_text("🆔 Kino ID raqamini yuboring.", reply_markup=ReplyKeyboardRemove())
    return KINO_ID


def kino_id(update: Update, context: CallbackContext):
    if not update.message.text.isdigit():
        update.message.reply_text("❗️Faqat son yuboring.")
        return KINO_ID
    context.user_data['kino_id'] = int(update.message.text)
    update.message.reply_text("🎥 Kinoni video ko'rinishida yuboring.")
    return VIDEO


def video_qabul(update: Update, context: CallbackContext):
    if update.message.video:
        context.user_data['file_id'] = update.message.video.file_id
        update.message.reply_text("📛 Kino nomini yuboring.")
        return NOMI
    else:
        update.message.reply_text("❗️Iltimos, video yuboring.")
        return VIDEO


def kino_nomi(update: Update, context: CallbackContext):
    nomi = update.message.text
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO kinolar (id, file_id, nomi) VALUES (?, ?, ?)", (
            context.user_data['kino_id'],
            context.user_data['file_id'],
            nomi
        ))
        con.commit()
        update.message.reply_text("✅ Kino muvaffaqiyatli saqlandi!", reply_markup=admin_menu)
    except sqlite3.IntegrityError:
        update.message.reply_text("❌ Bu ID allaqachon mavjud!", reply_markup=admin_menu)
    finally:
        con.close()
    return ConversationHandler.END


# Kino ko'rish
def kino_korish(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    # Foydalanuvchini bazaga qo'shish
    foydalanuvchi_qosh(user_id, user.username, user.first_name, user.last_name)

    # Admin uchun obuna tekshirmaymiz
    if user_id != ADMIN_ID:
        # Oddiy foydalanuvchilar uchun obuna tekshirish
        if not check_subscription(user_id, context):
            show_channels_menu(update, context)
            return

    if update.message.text.isdigit():
        kino_id = int(update.message.text)
        con = sqlite3.connect('kino_bot.db')
        cur = con.cursor()
        cur.execute("SELECT file_id, nomi FROM kinolar WHERE id = ?", (kino_id,))
        row = cur.fetchone()
        con.close()
        if row:
            context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=row[0],
                caption=f"🎬 {row[1]}\n\n✅ Sizga yoqadi degan umiddamiz!",
                reply_markup=user_menu if user_id != ADMIN_ID else admin_menu
            )
        else:
            update.message.reply_text("❌ Bunday ID topilmadi.")
    else:
        if update.effective_user.id == ADMIN_ID:
            update.message.reply_text("❗️ID yuboring yoki menyudan foydalaning.", reply_markup=admin_menu)
        else:
            update.message.reply_text("❗️Faqat raqam yuboring.")


# 🗑 Kino o'chirish
def ochirish_menu(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    update.message.reply_text("🗑 O'chirish uchun kino ID yuboring.", reply_markup=ReplyKeyboardRemove())
    return KINO_ID


def ochirish_kino(update: Update, context: CallbackContext):
    if not update.message.text.isdigit():
        update.message.reply_text("❗️Faqat son yuboring.")
        return KINO_ID
    kino_id = int(update.message.text)
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    cur.execute("SELECT nomi FROM kinolar WHERE id = ?", (kino_id,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM kinolar WHERE id = ?", (kino_id,))
        con.commit()
        update.message.reply_text(f"✅ '{row[0]}' nomli kino o'chirildi.", reply_markup=admin_menu)
    else:
        update.message.reply_text("❌ Bunday ID mavjud emas.", reply_markup=admin_menu)
    con.close()
    return ConversationHandler.END


# ❌ Menyu yopish
def menyuni_yopish(update: Update, context: CallbackContext):
    if update.effective_user.id == ADMIN_ID:
        update.message.reply_text("☑️ Menyu yopildi.", reply_markup=ReplyKeyboardRemove())


# Botni ishga tushirish
def main():
    baza_yarat()
    updater = Updater("8389090424:AAHTzrmjvCkp32jVucBT1f9_oJXdO5SI9-U", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    # Yangi handlerlar
    dp.add_handler(CallbackQueryHandler(check_subscription_callback, pattern='check_subs'))
    dp.add_handler(MessageHandler(Filters.regex(r'^🎬 Kinolar ro\'yxati$'), kinolar_royxati))
    dp.add_handler(MessageHandler(Filters.regex(r'^📋 Qanday ishlatish\?$'), qanday_ishlatish))
    dp.add_handler(MessageHandler(Filters.regex(r'^📊 Statistika$'), statistika))
    dp.add_handler(MessageHandler(Filters.regex(r'^📢 Reklama$'), reklama_boshlash))
    dp.add_handler(MessageHandler(Filters.regex(r'^📢 Reklama berish$'), reklama_berish))
    dp.add_handler(MessageHandler(Filters.regex(r'^❌ Menyu yopish$'), menyuni_yopish))
    dp.add_handler(MessageHandler(Filters.regex(r'^🎬 Kinolar$'), lambda u, c: None))  # Admin uchun

    # Reklama conversation handler
    dp.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'^📢 Reklama$'), reklama_boshlash)],
        states={
            REKLAMA: [MessageHandler(Filters.all & ~Filters.command, reklama_yuborish)],
        },
        fallbacks=[CommandHandler("cancel", reklama_bekor)]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'^➕ Qo\'sh$'), add_kino)],
        states={
            KINO_ID: [MessageHandler(Filters.text & ~Filters.command, kino_id)],
            VIDEO: [MessageHandler(Filters.video, video_qabul)],
            NOMI: [MessageHandler(Filters.text & ~Filters.command, kino_nomi)],
        },
        fallbacks=[CommandHandler("start", start)]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'^🗑 O\'chirish$'), ochirish_menu)],
        states={
            KINO_ID: [MessageHandler(Filters.text & ~Filters.command, ochirish_kino)],
        },
        fallbacks=[CommandHandler("start", start)]
    ))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, kino_korish))

    updater.bot.set_my_commands([
        BotCommand("start", "Botni ishga tushirish")
    ])

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
