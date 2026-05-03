import logging
import pandas as pd
import json
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "YOUR_TOKEN"
VIP_GROUP_ID = -YOUR_VIP_GROUP_ID
ACCOUNTS_FILE = "accounts.xlsx"
INVITE_LINKS_FILE = "invite_links.json"

logging.basicConfig(level=logging.INFO)

# --- دوال تحميل وحفظ روابط الدعوة ---
def load_invite_links():
    if os.path.exists(INVITE_LINKS_FILE):
        with open(INVITE_LINKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_invite_links(data):
    with open(INVITE_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- رسالة الترحيب مع الأزرار ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📥 اضغط لإدخال رقم الحساب", callback_data="enter_account"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 مرحبًا بك في بوت Nexora VIP\nيرجى اختيار أحد الخيارات التالية:",
        reply_markup=reply_markup
    )

# --- التعامل مع أزرار الترحيب ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "enter_account":
        context.user_data['awaiting_account'] = True
        await query.edit_message_text("📝 من فضلك أرسل رقم حسابك الآن.")
    elif query.data == "cancel":
        context.user_data['awaiting_account'] = False
        await query.edit_message_text("❌ تم إلغاء العملية.")

# --- التعامل مع رسالة رقم الحساب ---
async def handle_account_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_account', False):
        account_number = update.message.text.strip()
        user_id = str(update.effective_user.id)

        try:
            df = pd.read_excel(ACCOUNTS_FILE)
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في قراءة بيانات الحسابات. حاول لاحقاً.\n{e}")
            return

        if account_number not in df['account_number'].astype(str).values:
            await update.message.reply_text("❌ انت غير منضم تحت وكالتنا انقل حسابك ضمن وكالتنا.")
        else:
            balance = df.loc[df['account_number'].astype(str) == account_number, 'balance'].values[0]
            if balance < 50:
                await update.message.reply_text("⚠️ يجب أن يكون رصيد حسابك 50 دولار على الأقل.")
            else:
                try:
                    invite_links = load_invite_links()
                    chat = await context.bot.get_chat(VIP_GROUP_ID)

                    if account_number in invite_links:
                        if invite_links[account_number]["user_id"] != user_id:
                            await update.message.reply_text("❌ هذا الحساب مستخدم بالفعل من قبل مستخدم آخر.")
                            context.user_data['awaiting_account'] = False
                            return
                        invite_link = invite_links[account_number]["link"]
                    else:
                        invite = await chat.create_invite_link(
                            member_limit=1,
                            creates_join_request=False,
                            expire_date=None
                        )
                        invite_link = invite.invite_link
                        invite_links[account_number] = {
                            "link": invite_link,
                            "user_id": user_id,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        save_invite_links(invite_links)

                    await update.message.reply_text(
                        f"✅ تم التحقق من حسابك ويمكنك الانضمام إلى المجموعة VIP.\n\n"
                        f"🔗 رابط الانضمام الخاص بك:\n{invite_link}\n\n"
                        "⚠️ لا تشارك هذا الرابط مع الآخرين."
                    )
                except Exception as e:
                    await update.message.reply_text(f"❌ فشل في إنشاء رابط الدعوة.\n{e}")

        context.user_data['awaiting_account'] = False
    else:
        await update.message.reply_text("❌ الرجاء الضغط على الزر لإدخال رقم الحساب أولاً.")

# --- الوظيفة الرئيسية ---
async def main():
    import nest_asyncio
    nest_asyncio.apply()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_account_number))

    print("🤖 Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
