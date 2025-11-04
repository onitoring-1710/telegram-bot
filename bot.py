import os
import datetime
import asyncio
from fastapi import FastAPI
import uvicorn
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= Переменные окружения =================
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_ID = int(os.environ["USER_ID"])
USER_ID_OWNER = int(os.environ["USER_ID_OWNER"])

moscow_tz = datetime.timezone(datetime.timedelta(hours=3))

# ================= FastAPI сервер =================
app_web = FastAPI()

@app_web.get("/")
def root():
    return {"status": "Bot is alive"}

# ================= Функция отправки напоминаний =================
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Я выпила. ❤️", callback_data="drank")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=USER_ID,
        text="🔔 Напоминание, Дашуля! Уже 11:15, пора пить витамины. 🦊",
        reply_markup=reply_markup
    )
    await context.bot.send_sticker(
        chat_id=USER_ID,
        sticker="CAACAgIAAxkBAAE9XXRpCSA6OsGhJ0mtYB2IcNsbSg2eugACWwADVmQBFIoTkT5MbLkXNgQ"
    )

# ================= Обработка кнопки =================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "drank":
        await query.edit_message_text(text="Умничка, солнце. ❤️")
        await context.bot.send_message(chat_id=USER_ID_OWNER, text="✅ Дашуля выпила витамины.")

# ================= Работа с задачами =================
def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

# ================= Команды /start и /stop =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remove_job_if_exists("daily_reminder", context)
    context.job_queue.run_daily(
        send_reminder,
        time=datetime.time(hour=11, minute=15, tzinfo=moscow_tz),
        name="daily_reminder"
    )
    await update.message.reply_text("✅ Напоминания включены! Каждый день в 11:15.")
    await context.bot.send_message(chat_id=USER_ID_OWNER, text="✅ Дашуля включила напоминание.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remove_job_if_exists("daily_reminder", context)
    await update.message.reply_text("🛑 Напоминания остановлены.")
    await context.bot.send_message(chat_id=USER_ID_OWNER, text="🛑 Дашуля выключила напоминание.")

# ================= Основной запуск =================
async def main_async():
    # Telegram бот
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("stop", stop))
    app_bot.add_handler(CallbackQueryHandler(button_callback))

    # Uvicorn сервер
    config = uvicorn.Config(app_web, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    server = uvicorn.Server(config)

    # Запуск бота и FastAPI параллельно
    await asyncio.gather(
        server.serve(),
        app_bot.run_polling()
    )

if __name__ == "__main__":
    asyncio.run(main_async())
