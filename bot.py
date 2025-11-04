import datetime
import os
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, JobQueue
from fastapi import FastAPI
import threading
import uvicorn

# ================= Переменные окружения =================
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_ID = int(os.environ["USER_ID"])
USER_ID_OWNER = int(os.environ["USER_ID_OWNER"])

moscow_tz = datetime.timezone(datetime.timedelta(hours=3))

# ================= FastAPI для Keep Alive =================
app_web = FastAPI()

@app_web.get("/")
def root():
    return {"status": "Bot is alive"}

def start_webserver():
    uvicorn.run(app_web, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

# ================= Функция напоминания =================
def send_reminder(context):
    keyboard = [[InlineKeyboardButton("Я выпила. ❤️", callback_data="drank")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=USER_ID,
        text="🔔 Напоминание, Дашуля! Уже 11:15, пора пить витамины. 🦊",
        reply_markup=reply_markup
    )
    context.bot.send_sticker(
        chat_id=USER_ID,
        sticker="CAACAgIAAxkBAAE9XXRpCSA6OsGhJ0mtYB2IcNsbSg2eugACWwADVmQBFIoTkT5MbLkXNgQ"
    )

# ================= Обработка кнопки =================
def button_callback(update: Update, context):
    query = update.callback_query
    query.answer()
    if query.data == "drank":
        query.edit_message_text(text="Умничка, солнце. ❤️")
        context.bot.send_message(chat_id=USER_ID_OWNER, text="✅ Дашуля выпила витамины.")

# ================= Удаление задачи =================
def remove_job_if_exists(name: str, job_queue: JobQueue):
    current_jobs = job_queue.get_jobs_by_name(name)
    for job in current_jobs:
        job.schedule_removal()

# ================= Команды /start и /stop =================
def start(update: Update, context):
    remove_job_if_exists("daily_reminder", context.job_queue)
    # Запуск ежедневной задачи
    context.job_queue.run_daily(
        send_reminder,
        time=datetime.time(hour=11, minute=15, tzinfo=moscow_tz),
        context=context,
        name="daily_reminder"
    )
    update.message.reply_text("✅ Напоминания включены! Каждый день в 11:15.")
    context.bot.send_message(chat_id=USER_ID_OWNER, text="✅ Дашуля включила напоминание.")

def stop(update: Update, context):
    remove_job_if_exists("daily_reminder", context.job_queue)
    update.message.reply_text("🛑 Напоминания остановлены.")
    context.bot.send_message(chat_id=USER_ID_OWNER, text="🛑 Дашуля выключила напоминание.")

# ================= Основной запуск =================
def main():
    # Запуск FastAPI в отдельном потоке
    threading.Thread(target=start_webserver, daemon=True).start()

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
