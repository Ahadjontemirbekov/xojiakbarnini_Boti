import sqlite3
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)

# 🔐 Admin Telegram ID
ADMIN_ID = 6642743434  # <-- Faqat raqamlar, string emas

# Kino qo'shish va o'chirish bosqichlari
KINO_ID, VIDEO, NOMI = range(3)

# Admin menyusi
admin_menu = ReplyKeyboardMarkup([
    ['🎬 Kinolar'],
    ['➕ Qo\'sh', '🗑 O\'chirish'],
    ['❌ Menyu yopish']
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
    con.commit()
    con.close()

# /start buyrug'i
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        update.message.reply_text("🎥 Xush kelibsiz, admin!", reply_markup=admin_menu)
    else:
        update.message.reply_text("🎬 Xush kelibsiz!\n📥 Kino ko'rish uchun kino ID raqamini yuboring.")

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
    if update.message.text.isdigit():
        kino_id = int(update.message.text)
        con = sqlite3.connect('kino_bot.db')
        cur = con.cursor()
        cur.execute("SELECT file_id, nomi FROM kinolar WHERE id = ?", (kino_id,))
        row = cur.fetchone()
        con.close()
        if row:
            context.bot.send_video(chat_id=update.effective_chat.id, video=row[0], caption=f"Kino: {row[1]}")
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
    updater = Updater("7740683127:AAHgwv0hMiwdxXPUAx345u9l6SN58NnTWlw", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(MessageHandler(Filters.regex(r'^❌ Menyu yopish$'), menyuni_yopish))
    dp.add_handler(MessageHandler(Filters.regex(r'^🎬 Kinolar$'), kino_korish))

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
