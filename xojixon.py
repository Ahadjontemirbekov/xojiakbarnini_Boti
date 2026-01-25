import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import google.generativeai as genai

# =======================
# .env yuklash
# =======================
load_dotenv()

# Tog'ri: faqat o'zgaruvchi nomi
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("❌ TELEGRAM_TOKEN yoki GEMINI_API_KEY topilmadi")
    print("📁 .env faylini tekshiring:")
    print(f"   TELEGRAM_TOKEN mavjudmi: {'Ha' if TELEGRAM_TOKEN else 'Yoq'}")
    print(f"   GEMINI_API_KEY mavjudmi: {'Ha' if GEMINI_API_KEY else 'Yoq'}")
    raise ValueError("Tokenlar topilmadi (.env ni tekshir)")

print("✅ Tokenlar muvaffaqiyatli yuklandi")

# =======================
# Gemini client
# =======================
genai.configure(api_key=GEMINI_API_KEY)  # Tog'ri sozlash usuli
MODEL_NAME = "gemini-2.5-flash"

# Har bir foydalanuvchi uchun chat xotirasi
user_chats = {}


# =======================
# /start
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat.id
    user_chats[chat_id] = []

    await update.message.reply_text(
        "🤖 Salom! Men **Gemini AI** bilan ishlaydigan botman.\n\n"
        "📌 Xususiyatlar:\n"
        "• Juda tez (Gemini 2.5 Flash)\n"
        "• Uzbek tilini tushunadi\n"
        "• Suhbat xotirasiga ega\n"
        "• Xavfsiz (.env)\n\n"
        "Buyruqlar:\n"
        "/start - Yangi suhbat\n"
        "/clear - Suhbatni tozalash\n"
        "/help - Yordam"
    )


# =======================
# /help
# =======================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "📚 **Yordam**\n\n"
        "Menga oddiy xabar yuboring:\n"
        "• Kod yozish\n"
        "• Savollarga javob\n"
        "• Tarjima\n"
        "• Maslahat\n\n"
        "⚡️ Model: Gemini 2.5 Flash\n"
        "💬 Faqat shaxsiy chatda ishlaydi"
    )


# =======================
# /clear
# =======================
async def clear_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat.id
    user_chats[chat_id] = []

    await update.message.reply_text("✅ Suhbat tozalandi!")


# =======================
# Xabarlar
# =======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat.id
    user_text = update.message.text

    # typing...
    await update.message.chat.send_action("typing")

    try:
        # Gemini AI dan javob olish
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(user_text)

        ai_text = response.text

        if len(ai_text) > 4096:
            for i in range(0, len(ai_text), 4096):
                await update.message.reply_text(ai_text[i:i + 4096])
        else:
            await update.message.reply_text(ai_text)

    except Exception as e:
        await update.message.reply_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        print(f"❌ Xatolik: {str(e)}")


# =======================
# MAIN
# =======================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_conversation))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
            handle_message
        )
    )

    print("=" * 50)
    print("🤖 Bot ishga tushdi...")
    print(f"📝 Chat ID: {TELEGRAM_TOKEN[:15]}...")  # Tokenning faqat birinchi 15 belgisi
    print("⚡️ Model: Gemini 2.5 Flash")
    print("🔐 API KEY .env orqali")
    print("=" * 50)


    app.run_polling()


if __name__ == "__main__":
    main()
