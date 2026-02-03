import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ["BOT_TOKEN"]  # токен берем из переменной окружения
ADMIN_IDS = {1305284308}  # сюда можно добавить других админов

IMAGE_WELCOME = "1.jpg"
IMAGE_MAP = "2.jpg"
DB_FILE = "users.db"  # SQLite база

# ===== DATABASE =====
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # таблица участников
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            will_come INTEGER
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, username, will_come_flag):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if c.fetchone() is None:
        c.execute("INSERT INTO users (id, username, will_come) VALUES (?, ?, ?)",
                  (user_id, username, will_come_flag))
    conn.commit()
    conn.close()

def user_exists(user_id, will_come_flag):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ? AND will_come = ?", (user_id, will_come_flag))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def count_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE will_come = 1")
    will = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE will_come = 0")
    cant = c.fetchone()[0]
    conn.close()
    return will, cant

# ===== HELPERS =====
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Я обязательно буду", callback_data="will_come_btn"),
            InlineKeyboardButton("Я не смогу присутствовать", callback_data="cant_come_btn"),
        ]
    ]
    if is_admin(update.effective_user.id):
        keyboard.append([InlineKeyboardButton("Список участников", callback_data="show_list")])

    await update.message.reply_text(
        "Пожалуйста, выберите вариант:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== CALLBACK =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.full_name or str(user_id)

    # --- Я обязательно буду ---
    if query.data == "will_come_btn":
        if user_exists(user_id, 1):
            await query.message.reply_text("Вы уже записаны в список 'Я обязательно буду'.")
            return

        add_user(user_id, username, 1)

        if os.path.exists(IMAGE_WELCOME):
            with open(IMAGE_WELCOME, "rb") as img:
                await query.message.reply_photo(photo=img)

        await query.message.reply_text(
            """Дорогие гости!

Пожалуйста, примите к сведению, что сменная обувь с чистой подошвой для
выхода на лёд обязательна, без этого необходимого атрибута мы не сможем
допустить вас к игре👟❗️
Также недопустимо выходить на лёд в нетрезвом виде и брать еду и напитки с
собой!🥤🍿

Выполняя эти правила, вы помогаете нам сохранять отличное качество ледовой
площадки, что обеспечивает вам хорошую игру и времяпровождение💙
Просьба приезжать за 15-20 минут для заполнения анкет❄️

Пожалуйста, передайте это сообщение всем игрокам вашей компании. Будем рады видеть вас в кёрлинг-центре "Дом со льдом"
"""
        )

        keyboard = [
            [InlineKeyboardButton("Как найти", callback_data="how_to_find")],
            [InlineKeyboardButton(
                "Нужна помощь с подарком – держи готовый виш лист",
                url="https://ohmywishes.com/users/bb65b864ce08b81198850083/lists/66698133393f39d745158759"
            )]
        ]
        await query.message.reply_text(
            "Может быть полезно:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # --- Я не смогу присутствовать ---
    elif query.data == "cant_come_btn":
        if user_exists(user_id, 0):
            await query.message.reply_text("Вы уже отметились как 'не смогу присутствовать'.")
            return

        add_user(user_id, username, 0)
        await query.message.reply_text(":(")

    # --- Как найти ---
    elif query.data == "how_to_find":
        if os.path.exists(IMAGE_MAP):
            with open(IMAGE_MAP, "rb") as img:
                await query.message.reply_photo(photo=img)

    # --- Список участников (для админа) ---
    elif query.data == "show_list":
        if not is_admin(user_id):
            return
        will, cant = count_users()
        await query.message.reply_text(f"Количество участников, которые придут: {will}\nКоличество участников, которые не придут: {cant}")

# ===== MAIN =====
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
