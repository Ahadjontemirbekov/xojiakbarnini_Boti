import sqlite3
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    BotCommand
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
    Filters
)

# 🔐 Admin Telegram ID
ADMIN_ID = 6659797188
ADMIN_USERNAME = "@xoji_4"

# 📢 Majburiy obuna kanallari
REQUIRED_CHANNELS = [
    {"name": "1 - Kanal", "username": "@jaga_group", "url": "https://t.me/jaga_group"}
]

# Bosqichlar
KINO_ID, VIDEO, NOMI = range(3)
REKLAMA = 4

# Menyular
admin_menu = ReplyKeyboardMarkup([
    ['🎬 Kinolar', '📊 Statistika'],
    ['➕ Qo\'sh', '🗑 O\'chirish'],
    ['📢 Reklama', '❌ Menyu yopish']
], resize_keyboard=True)

user_menu = ReplyKeyboardMarkup([
    ['🎬 Kinolar ro\'yxati', '📋 Qanday ishlatish?'],
    ['📢 Reklama berish']
], resize_keyboard=True)


# --- BAZA BILAN ISHLASH ---
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


def foydalanuvchi_qosh(user_id, username, first_name, last_name):
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT OR IGNORE INTO foydalanuvchilar (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name))
        con.commit()
    except:
        pass
    finally:
        con.close()


def barcha_foydalanuvchilarni_ol():
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    cur.execute("SELECT user_id FROM foydalanuvchilar")
    users = [row[0] for row in cur.fetchall()]
    con.close()
    return users


# --- TEKSHIRUV ---
def check_subscription(bot, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=channel["username"], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True


def show_channels_menu(update, context):
    buttons = [[InlineKeyboardButton(c['name'], url=c['url'])] for c in REQUIRED_CHANNELS]
    buttons.append([InlineKeyboardButton("✅ Obuna bo'ldim", callback_data='check_subs')])
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text("⚠️ Quyidagi kanalga obuna bo'ling!", reply_markup=reply_markup)


# --- HANDLERLAR ---
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    foydalanuvchi_qosh(user.id, user.username, user.first_name, user.last_name)

    if user.id == ADMIN_ID:
        update.message.reply_text("🎥 Xush kelibsiz, admin!", reply_markup=admin_menu)
        return

    if not check_subscription(context.bot, user.id):
        show_channels_menu(update, context)
        return

    update.message.reply_text("🎬 Xush kelibsiz!\n📥 Kino ID raqamini yuboring.", reply_markup=user_menu)


def check_subscription_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if check_subscription(context.bot, user_id):
        query.edit_message_text("✅ Obuna tasdiqlandi!")
        context.bot.send_message(user_id, "Menyu:", reply_markup=user_menu)
    else:
        query.edit_message_text("❌ Obuna topilmadi! Iltimos obuna bo‘ling.")
        # Qayta ko'rsatish
        buttons = [[InlineKeyboardButton(c['name'], url=c['url'])] for c in REQUIRED_CHANNELS]
        buttons.append([InlineKeyboardButton("✅ Obuna bo'ldim", callback_data='check_subs')])
        context.bot.send_message(user_id, "⚠️ Obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(buttons))


def statistika(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID: return
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM kinolar");
    kinolar_soni = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM foydalanuvchilar");
    jami = cur.fetchone()[0]

    now = datetime.now()
    cur.execute("SELECT COUNT(*) FROM foydalanuvchilar WHERE joined_date > ?", (now - timedelta(days=1),));
    kunlik = cur.fetchone()[0]

    update.message.reply_text(f"📊 Statistika:\n🎬 Kinolar: {kinolar_soni}\n👥 Jami: {jami}\n📈 Bugun: {kunlik}",
                              reply_markup=admin_menu)
    con.close()


# --- REKLAMA ---
def reklama_boshlash(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID: return
    update.message.reply_text("📢 Reklama yuboring. Bekor qilish: /cancel", reply_markup=ReplyKeyboardRemove())
    return REKLAMA


def reklama_yuborish(update: Update, context: CallbackContext):
    users = barcha_foydalanuvchilarni_ol()
    successful, failed = 0, 0
    msg = update.message

    for user_id in users:
        try:
            context.bot.copy_message(chat_id=user_id, from_chat_id=msg.chat_id, message_id=msg.message_id)
            successful += 1
        except:
            failed += 1

    update.message.reply_text(f"✅ Tugadi!\nSifatli: {successful}\nXato: {failed}", reply_markup=admin_menu)
    return ConversationHandler.END


# --- KINO QO'SHISH ---
def add_kino(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID: return
    update.message.reply_text("🆔 Kino ID yuboring:", reply_markup=ReplyKeyboardRemove())
    return KINO_ID


def kino_id_get(update: Update, context: CallbackContext):
    if not update.message.text.isdigit():
        update.message.reply_text("Faqat son!")
        return KINO_ID
    context.user_data['kino_id'] = int(update.message.text)
    update.message.reply_text("🎥 Videoni yuboring.")
    return VIDEO


def video_qabul(update: Update, context: CallbackContext):
    if not update.message.video:
        update.message.reply_text("Video yuboring!")
        return VIDEO
    context.user_data['file_id'] = update.message.video.file_id
    update.message.reply_text("📛 Nomini yuboring.")
    return NOMI


def kino_nomi_save(update: Update, context: CallbackContext):
    nomi = update.message.text
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO kinolar (id, file_id, nomi) VALUES (?, ?, ?)",
                    (context.user_data['kino_id'], context.user_data['file_id'], nomi))
        con.commit()
        update.message.reply_text("✅ Saqlandi!", reply_markup=admin_menu)
    except:
        update.message.reply_text("❌ ID band!", reply_markup=admin_menu)
    finally:
        con.close()
    return ConversationHandler.END


# --- KINO KO'RISH ---
def kino_korish(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and not check_subscription(context.bot, user_id):
        show_channels_menu(update, context)
        return

    text = update.message.text
    if text and text.isdigit():
        con = sqlite3.connect('kino_bot.db')
        cur = con.cursor()
        cur.execute("SELECT file_id, nomi FROM kinolar WHERE id=?", (int(text),))
        row = cur.fetchone()
        con.close()

        if row:
            update.message.reply_video(video=row[0], caption=f"🎬 {row[1]}")
        else:
            update.message.reply_text("❌ Topilmadi.")
    else:
        update.message.reply_text("ID yuboring.")


def ochirish_menu(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID: return
    update.message.reply_text("🗑 O'chirish uchun ID yuboring:", reply_markup=ReplyKeyboardRemove())
    return KINO_ID


def ochirish_kino_db(update: Update, context: CallbackContext):
    if not update.message.text.isdigit(): return KINO_ID
    kid = int(update.message.text)
    con = sqlite3.connect('kino_bot.db')
    cur = con.cursor()
    cur.execute("DELETE FROM kinolar WHERE id=?", (kid,))
    con.commit()
    con.close()
    update.message.reply_text("✅ O'chirildi.", reply_markup=admin_menu)
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text("Bekor qilindi.", reply_markup=admin_menu)
    return ConversationHandler.END


def main():
    baza_yarat()
    # Tokenni kiriting
    updater = Updater("8389090424:AAHTzrmjvCkp32jVucBT1f9_oJXdO5SI9-U")
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(check_subscription_callback, pattern='check_subs'))

    # Conversationlar
    dp.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^📢 Reklama$'), reklama_boshlash)],
        states={REKLAMA: [MessageHandler(Filters.all & ~Filters.command, reklama_yuborish)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^➕ Qo\'sh$'), add_kino)],
        states={
            KINO_ID: [MessageHandler(Filters.text & ~Filters.command, kino_id_get)],
            VIDEO: [MessageHandler(Filters.video, video_qabul)],
            NOMI: [MessageHandler(Filters.text & ~Filters.command, kino_nomi_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^🗑 O\'chirish$'), ochirish_menu)],
        states={KINO_ID: [MessageHandler(Filters.text & ~Filters.command, ochirish_kino_db)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    dp.add_handler(MessageHandler(Filters.regex('^📊 Statistika$'), statistika))
    dp.add_handler(MessageHandler(Filters.regex('^🎬 Kinolar$') | Filters.text & ~Filters.command, kino_korish))

    updater.bot.set_my_commands([
        BotCommand("start", "Botni boshlash"),
    ])
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

