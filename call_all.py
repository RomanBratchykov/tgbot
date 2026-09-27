import sqlite3
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import os

TOKEN = os.environ["BOT_TOKEN"]
DB = "users.db"

def init_db():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            PRIMARY KEY (chat_id, user_id)
        )
    """)
    con.commit()
    con.close()

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None or chat.type == "private":
        return
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT OR REPLACE INTO users (chat_id, user_id, username, full_name) VALUES (?, ?, ?, ?)",
        (chat.id, user.id, user.username, user.full_name),
    )
    con.commit()
    con.close()

async def call_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT user_id, username, full_name FROM users WHERE chat_id = ?", (chat_id,)
    ).fetchall()
    con.close()

    if not rows:
        await update.message.reply_text("No known users yet — they need to send a message first.")
        return

    mentions = []
    for user_id, username, full_name in rows:
        if username:
            mentions.append(f"@{username}")
        else:
            # users without a public username still get a working mention link
            mentions.append(f"[{full_name}](tg://user?id={user_id})")

    text = " ".join(mentions)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("all", call_all))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, register_user))
    app.add_handler(CommandHandler("start", register_user))  # also register on /start etc.
    app.run_polling()

if __name__ == "__main__":
    main()