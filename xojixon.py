from telegram.ext import Updater,CommandHandler,MessageHandler,Filters
from telegram import KeyboardButton,ReplyKeyboardMarkup

def start_bosganda(update,context):
    k=[
        [KeyboardButton(text="Heshteg")]
    ]
    r=ReplyKeyboardMarkup(k,resize_keyboard=True,one_time_keyboard=True)
    print(update.message.from_user)
    update.message.reply_text(text="salom",parse_mode="MarkdownV2",reply_markup=r)

def yuborilgan_xabar(update,context):
    text=update.message.text
    if text=="Heshteg":
        k=[
            [KeyboardButton(text="2M thank you🍋")]
        ]
        r = ReplyKeyboardMarkup(k, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(text='salom',reply_markup=r)
    elif text=="2M thank you🍋":
        update.message.reply_text(text="""
                2M thank you🍋

#bnwphotography #shermuhammedoff  #photograph #newbornphotography #photogram #portraitphotography #iphonephotography #blackandwhitephotography #photos #photographyislifee #weddingphotographer #dronephotography #landscapephotography #foodphotography #architecturephotography #photographylover #shermuhammedoff  #streetphotographer #fashionphotography #urbanphotography #photographysouls #photomodel #travelphoto #photographyislife #photographie #fashionphotographer #photographers #lifestylephotography #toyphotography #canon_photos #shermuhammedoff  #familyphotography #filmphotography
#qandiyor_bro #tushuncha_ol #muh1ddinov.083
                """)



def main():
    updater=Updater(token="7823878057:AAHFDjRYRgi24279DYz5PRq7byaPflGckRQ",use_context=True)
    dp=updater.dispatcher
    dp.add_handler(CommandHandler("start",start_bosganda))
    dp.add_handler(MessageHandler(Filters.text,yuborilgan_xabar))
    updater.start_polling()
    updater.idle()
if __name__=="__main__":
    main()
