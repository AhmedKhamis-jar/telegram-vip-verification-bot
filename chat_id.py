from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "YOUR_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("أهلا بك في البوت. أرسل أي رسالة وسأقوم بإرجاع معرف الجروب إذا أضفتني في جروب.")

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat_id
        await update.message.reply_text(f"📌 معرف الجروب أو الدردشة هو:\n`{chat_id}`", parse_mode='Markdown')

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, get_chat_id))
    app.run_polling()

if __name__ == "__main__":
    main()
