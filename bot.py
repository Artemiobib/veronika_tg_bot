import os
import json
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

import gspread
from google.oauth2.service_account import Credentials

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8255308627:AAEbNn7mNntwXeGFfQe8dtn--0fSFZmyMcA"

# админы через запятую
ADMIN_IDS = {
    1305284308,
    1166038087,
}

SPREADSHEET_NAME = "veronikabd"

# ===== GOOGLE SHEETS =====
def get_sheet():
    creds_info = json.loads(os.environ["GOOGLE_CREDS"])
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Я обязательно буду", callback_data="will_come")],
        [InlineKeyboardButton("Я не смогу присутствовать", callback_data="wont_come")]
    ]

    if update.effective_user.id in ADMIN_IDS:
        keyboard.append(
            [InlineKeyboardButton("📊 Список участников", callback_data="stats")]
        )

    await update.message.reply_text(
        "Пожалуйста, выберите вариант:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===== КНОПКИ =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data
    sheet = get_sheet()

    # ===== ВЫБОР ПОЛЬЗОВАТЕЛЯ =====
    if data in ("will_come", "wont_come"):
        rows = sheet.get_all_values()[1:]  # без заголовка
        row_index = None

        for i, row in enumerate(rows, start=2):
            if row and row[0] == str(user.id):
                row_index = i
                break

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if row_index:
            sheet.update(
                f"D{row_index}:E{row_index}",
                [[data, now]]
            )
        else:
            sheet.append_row([
                user.id,
                user.username or "",
                user.full_name,
                data,
                now
            ])

        if data == "will_come":
            await query.message.reply_text("🎉 Отлично! Мы вас ждём.")
        else:
            await query.message.reply_text(":(")

    # ===== СТАТИСТИКА АДМИНА =====
    elif data == "stats" and user.id in ADMIN_IDS:
        rows = sheet.get_all_values()[1:]

        will_come = sum(1 for r in rows if len(r) > 3 and r[3] == "will_come")
        wont_come = sum(1 for r in rows if len(r) > 3 and r[3] == "wont_come")

        await query.message.reply_text(
            f"📊 Статистика:\n\n"
            f"Будут: {will_come}\n"
            f"Не смогут: {wont_come}"
        )


# ===== ЗАПУСК =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
