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
        ['Siyahi', 'Tapshiriq elave et'],
        ['Xatirlatma elave et', 'Tamamla'],
        ['Sil', 'Komek']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! Men senin shexsi komekcinam!\n\nAsagidaki duymelerden istifade et:",
        reply_markup=get_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Emrler:\n\n"
        "/add Metn - tapshiriq elave et\n"
        "/list - siyahini goster\n"
        "/done 1 - 1-ci tapshiriqi tamamla\n"
        "/delete 1 - 1-ci tapshiriqi sil\n"
        "/remind TT.AA.IIII SS:DD Metn - xatirlatma qur\n\n"
        "Misal:\n"
        "/remind 25.06.2026 09:00 Anbari yoxla",
        reply_markup=get_keyboard()
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Tapshiriqi yaz:\n/add Yanacaq doldur")
        return
    task = ' '.join(context.args)
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (text, done, created) VALUES (?, 0, ?)",
              (task, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()
    await update.message.reply_text("Tapshiriq elave edildi:\n" + task, reply_markup=get_keyboard())

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("SELECT id, text, done FROM tasks ORDER BY done, id")
    tasks = c.fetchall()
    c.execute("SELECT id, text, remind_time, done FROM reminders ORDER BY done, remind_time")
    reminders = c.fetchall()
    conn.close()
    msg = "Tapshiriqler:\n"
    if tasks:
        for t in tasks:
            status = "OK" if t[2] else "---"
            msg += status + " [" + str(t[0]) + "] " + t[1] + "\n"
    else:
        msg += "Tapshiriq yoxdur\n"
    msg += "\nXatirlatmalar:\n"
    if reminders:
        for r in reminders:
            status = "OK" if r[3] else "---"
            msg += status + " [" + str(r[0]) + "] " + r[2] + " - " + r[1] + "\n"
    else:
        msg += "Xatirlatma yoxdur\n"
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
    await update.message.reply_text("Tapshiriq tamamlandi: #" + task_id, reply_markup=get_keyboard())

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
    await update.message.reply_text("Silindi: #" + task_id, reply_markup=get_keyboard())

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Format:\n/remind TT.AA.IIII SS:DD Metn\n\nMisal:\n/remind 25.06.2026 09:00 Anbari yoxla"
        )
        return
    try:
        date_str = context.args[0]
        time_str = context.args[1]
        text = ' '.join(context.args[2:])
        remind_time = datetime.strptime(date_str + " " + time_str, "%d.%m.%Y %H:%M")
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("INSERT INTO reminders (chat_id, text, remind_time, done) VALUES (?, ?, ?, 0)",
                  (update.message.chat_id, text, remind_time.strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
        await update.message.reply_text(
            "Xatirlatma quruldu!\nTarix: " + date_str + " " + time_str + "\nMetn: " + text,
            reply_markup=get_keyboard()
        )
    except Exception as e:
        await update.message.reply_text("Format sehvdir!\n/remind 25.06.2026 09:00 Anbari yoxla")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'Siyahi':
        await list_tasks(update, context)
    elif text == 'Tapshiriq elave et':
        await update.message.reply_text("Tapshiriqi yaz:\n/add Metn")
    elif text == 'Xatirlatma elave et':
        await update.message.reply_text("Format:\n/remind 25.06.2026 09:00 Anbari yoxla")
    elif text == 'Tamamla':
        await update.message.reply_text("ID yaz:\n/done 1")
    elif text == 'Sil':
        await update.message.reply_text("ID yaz:\n/delete 1")
    elif text == 'Komek':
        await help_cmd(update, context)
    else:
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("INSERT INTO tasks (text, done, created) VALUES (?, 0, ?)",
                  (text, datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
        await update.message.reply_text("Qeyd saxlandi:\n" + text, reply_markup=get_keyboard())

async def check_reminders(app):
    while True:
        try:
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            c.execute("SELECT id, chat_id, text FROM reminders WHERE remind_time=? AND done=0", (now,))
            due = c.fetchall()
            for r in due:
                await app.bot.send_message(chat_id=r[1], text="XATIRLATMA!\n\n" + r[2])
                c.execute("UPDATE reminders SET done=1 WHERE id=?", (r[0],))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Reminder error: " + str(e))
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

if __name__ == "__main__":
    main()

