import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

BOT_TOKEN = "8938350975:AAHBNcMOGITyVBlS_iI0bOGATCgk8C-VOv4"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, text TEXT, done INTEGER DEFAULT 0, created TEXT)''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! Mən sənin şəxsi assistanınım! 🤖\n\n"
        "/add - Tapşırıq əlavə et\n"
        "/list - Tapşırıqları göstər\n"
        "/done - Tapşırığı tamamla\n"
        "/delete - Tapşırığı sil\n"
        "/help - Kömək"
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Tapşırığı yaz: /add Yanacaq doldur")
        return
    task = ' '.join(context.args)
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (text, done, created) VALUES (?, 0, ?)",
              (task, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Əlavə edildi: {task}")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("SELECT id, text, done, created FROM tasks ORDER BY done, id")
    tasks = c.fetchall()
    conn.close()
    if not tasks:
        await update.message.reply_text("📋 Tapşırıq yoxdur!")
        return
    msg = "📋 Tapşırıqların:\n\n"
    for t in tasks:
        status = "✅" if t[2] else "⏳"
        msg += f"{status} [{t[0]}] {t[1]}\n"
    await update.message.reply_text(msg)

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ID yaz: /done 1")
        return
    task_id = context.args[0]
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Tapşırıq #{task_id} tamamlandı!")

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ID yaz: /delete 1")
        return
    task_id = context.args[0]
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🗑 Tapşırıq #{task_id} silindi!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (text, done, created) VALUES (?, 0, ?)",
              (text, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"📝 Qeyd saxlandı: {text}\n\n/list ilə bax")

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("delete", delete_task))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()