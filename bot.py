import logging
import sqlite3
from datetime import datetime
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8938350975:AAHBNcMOGITyVBlS_iI0bOGATCgk8C-VOv4"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, text TEXT, done INTEGER DEFAULT 0, created TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders
                 (id INTEGER PRIMARY KEY, chat_id INTEGER, text TEXT, remind_time TEXT, done INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_keyboard():
    keyboard = [
        ['📋 Siyahı', '➕ Tapşırıq əlavə et'],
        ['⏰ Xatırlatma əlavə et', '✅ Tamamla'],
        ['🗑️ Sil', '❓ Kömək']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! Mən sənin şəxsi köməkçinəm! 🤖\n\n"
        "Aşağıdakı düymələrdən istifadə et və ya əmr yaz:",
        reply_markup=get_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Əmrlər:\n\n"
        "/add Mətn — tapşırıq əlavə et\n"
        "/list — siyahını göstər\n"
        "/done 1 — 1-ci tapşırığı tamamla\n"
        "/delete 1 — 1-ci tapşırığı sil\n"
        "/remind TT.AA.İİİİ SS:DD Mətn — xatırlatma qur\n\n"
        "Misal:\n"
        "/remind 25.06.2026 09:00 Anbarı yoxla\n\n"
        "Və ya sadəcə mətn yaz — qeyd kimi saxlanır!",
        reply_markup=get_keyboard()
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Tapşırığı yaz:\n/add Yanacaq doldur")
        return
    task = ' '.join(context.args)
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (text, done, created) VALUES (?, 0, ?)",
              (task, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Tapşırıq əlavə edildi:\n{task}", reply_markup=get_keyboard())

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("SELECT id, text, done, created FROM tasks ORDER BY done, id")
    tasks = c.fetchall()
    c.execute("SELECT id, text, remind_time, done FROM reminders ORDER BY done, remind_time")
    reminders = c.fetchall()
    conn.close()

    msg = ""

    if tasks:
        msg += "📋 Tapşırıqlar:\n"
        for t in tasks:
            status = "✅" if t[2] else "⏳"
            msg += f"{status} [{t[0]}] {t[1]}\n"
    else:
        msg += "📋 Tapşırıq yoxdur\n"

    msg += "\n"

    if reminders:
        msg += "⏰ Xatırlatmalar:\n"
        for r in reminders:
            status = "✅" if r[3] else "🔔"
            msg += f"{status} [{r[0]}] {r[2]} — {r[1]}\n"
    else:
        msg += "⏰ Xatırlatma yoxdur\n"

    await update.message.reply_text(msg, reply_markup=get_keyboard())

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ID yaz:\n/done 1")
        return
    task_id = context.args[0]
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Tapşırıq #{task_id} tamamlandı!", reply_markup=get_keyboard())

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ID yaz:\n/delete 1")
        return
    task_id = context.args[0]
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    c.execute("DELETE FROM reminders WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🗑️ #{task_id} silindi!", reply_markup=get_keyboard())

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Format:\n/remind TT.AA.İİİİ SS:DD Mətn\n\n"
            "Misal:\n/remind 25.06.2026 09:00 Anbarı yoxla"
        )
        return
    try:
        date_str = context.args[0]
        time_str = context.args[1]
        text = ' '.join(context.args[2:])
        remind_time = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("INSERT INTO reminders (chat_id, text, remind_time, done) VALUES (?, ?, ?, 0)",
                  (update.message.chat_id, text, remind_time.strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
        await update.message.reply_text(
            f"🔔 Xatırlatma quruldu!\n\n"
            f"📅 Tarix: {date_str} {time_str}\n"
            f"📝 Mətn: {text}",
            reply_markup=get_keyboard()
        )
    except:
        await update.message.reply_text(
            "❌ Format səhvdir!\n\n"
            "Düzgün format:\n/remind 25.06.2026 09:00 Anbarı yoxla"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == '📋 Siyahı':
        await list_tasks(update, context)
    elif text == '➕ Tapşırıq əlavə et':
        await update.message.reply_text("Tapşırığı yaz:\n/add Mətn")
    elif text == '⏰ Xatırlatma əlavə et':
        await update.message.reply_text(
            "Format:\n/remind 25.06.2026 09:00 Anbarı yoxla"
        )
    elif text == '✅ Tamamla':
        await update.message.reply_text("ID yaz:\n/done 1")
    elif text == '🗑️ Sil':
        await update.message.reply_text("ID yaz:\n/delete 1")
    elif text == '❓ Kömək':
        await help_cmd(update, context)
    else:
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("INSERT INTO tasks (text, done, created) VALUES (?, 0, ?)",
                  (text, datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"📝 Qeyd saxlandı:\n{text}\n\n/list ilə bax", reply_markup=get_keyboard())

async def check_reminders(app):
    while True:
        try:
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            c.execute("SELECT id, chat_id, text FROM reminders WHERE remind_time=? AND done=0", (now,))
            due = c.fetchall()
            for r in due:
                await app.bot.send_message(
                    chat_id=r[1],
                    text=f"🔔 XATIRLATMA!\n\n{r[2]}"
                )
                c.execute("UPDATE reminders SET done=1 WHERE id=?", (r[0],))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Reminder error: {e}")
        await asyncio.sleep(60)

async def post_init(app):
    asyncio.create_task(check_reminders(app))

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("delete", delete_task))
    app.add_handler(CommandHandler("remind", add_reminder))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if _name_ == '_main_':
    main()
