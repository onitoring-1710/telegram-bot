import datetime
import os
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from fastapi import FastAPI
import uvicorn

BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_ID = int(os.environ["USER_ID"])
USER_ID_OWNER = int(os.environ["USER_ID_OWNER"])

moscow_tz = datetime.timezone(datetime.timedelta(hours=3))

# === Функция, которая шлёт напоминание с кнопкой ===
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

# === Обработка нажатия кнопки ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # обязательно, чтобы убрать "часики" на кнопке

    if query.data == "drank":
        # Редактируем сообщение — убираем кнопку
        await query.edit_message_text(text="Умничка, солнце. ❤️")
        # Отправляем подтверждение пользователю
        await context.bot.send_message(chat_id=USER_ID_OWNER, text="✅ Дашуля выпила витамины.")

# === Удаление задачи (если есть) ===
def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remove_job_if_exists("daily_reminder", context)

    context.job_queue.run_daily(
        send_reminder,
        time=datetime.time(hour=11, minute=15, tzinfo=moscow_tz),
        name="daily_reminder"
    )

    await update.message.reply_text("✅ Напоминания включены! Каждый день в 11:15.")
    await context.bot.send_message(chat_id=USER_ID_OWNER, text="✅ Дашуля включила напоминание.")

# === Команда /stop ===
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remove_job_if_exists("daily_reminder", context)
    await update.message.reply_text("🛑 Напоминания остановлены.")
    await context.bot.send_message(chat_id=USER_ID_OWNER, text="🛑 Дашуля выключила напоминание.")

# === FastAPI сервер для Keep Alive ===
app = FastAPI()

@app.get("/")
def root():
    return {"status": "Bot is alive"}

def start_webserver():
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

# === Основной запуск ===
def main():
    # Запуск FastAPI сервера в отдельном потоке
    threading.Thread(target=start_webserver, daemon=True).start()

    # Telegram бот
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("stop", stop))
    app_bot.add_handler(CallbackQueryHandler(button_callback))  # обработка кнопки

    app_bot.run_polling()

if __name__ == "__main__":
    main()