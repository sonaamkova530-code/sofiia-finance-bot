from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from states import ExpenseState, IncomeState, SettingsState
from telebot import types
from telebot import asyncio_filters
import keyboards
import secrets
import functools
import currency
import platform
import os
import math
import signal
from dotenv import load_dotenv
import asyncio
import reports
from database import Database
from datetime import datetime
import logging
from bot_service import BotService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
logging.basicConfig(
level=logging.INFO,
filename='bot.log',
format = '%(asctime)s - %(levelname)s - %(message)s',)
load_dotenv()

class Config:
    TOKEN = os.getenv("TOKEN")
    DAILY_LIMIT= float(os.getenv("DAILY_LIMIT", 500))
    MONTHLY_LIMIT = 5000
    DB_NAME = "my_budget.db"
    PRIMARY_CURRENCY = os.getenv("CURRENCY_PRIMARY", "EUR")
state_storage = StateMemoryStorage()
bot = AsyncTeleBot(Config.TOKEN, state_storage=state_storage)
bot.add_custom_filter(asyncio_filters.StateFilter(bot))
db = Database(Config.DB_NAME)
scheduler = AsyncIOScheduler()

class Validator:
    @staticmethod
    def parse_amount(text):
        try:
            amount = float(text.replace(",", "."))
            if amount < 0:
                return None, "Сума має бути більшою за 0."
            if amount > 1000000:
                return None, "Ого, сума занадто велика. Перевір ще раз."
            return amount, None
        except ValueError:
            return None, "Будь ласка, введи суму цифрами (наприклад: 105.45)"


async def send_weekly_report():
    user_id = 5096558702
    current_week_data = await db.get_weekly_stats(user_id)
    current_week_total = sum(row[1] for row in current_week_data) if current_week_data else 0
    last_week_total = await db.get_last_week(user_id)

    if current_week_total == 0 and last_week_total == 0:
        return

    diff = current_week_total - last_week_total

    if last_week_total > 0:
        percent = (diff / last_week_total) * 100
    else:
        percent = 100 if current_week_total > 0 else 0

    if diff > 0:
        trend = f"Це на *{abs(int(percent))}% більше*, ніж минулого тижня. Час пригальмувати з витратами!"
    elif diff < 0:
        trend = f"Це на *{abs(int(percent))}% менше*, ніж минулого тижня. Так тримати!"
    else:
        trend = "Витратила точно ту ж суму як минулого тижня. Стабільність!"

    report_text = (
        f"*Твій щотижневий фінансовий аналіз*\n\n"
        f"Цього тижня: *{current_week_total} ₴*\n"
        f"Минулого тижня: *{last_week_total} ₴*\n"
        f"{trend}\n\n"
        f"Детальніше на [Дашборді](http://127.0.0.1:8001/dashboard/{user_id})"
        )
    await bot.send_message(user_id, report_text, parse_mode="Markdown")



def log_action(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        print(f"--- [LOG] Виклик функції: {func.__name__} ---")
        result = await func(*args, **kwargs)
        print(f"--- [LOG] Функція {func.__name__} завершена ---")
        return result
    return wrapper

def error_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = (f"*Критична помилка:*\n\n"
            f"📌 *Функція:* `{func.__name__}`\n"
                f"⚠️ *Тип:* `{type(e).__name__}`\n"
                f"📝 *Текст:* `{e}`\n\n"
                f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(f"[ERROR] {error_msg}")

        try:
            await bot.send_message(5096558702, error_msg, parse_mode="Markdown")
        except Exception as bot_error:
            print(f"Навіть повідомлення про помилку не відправилось: {bot_error}")
            return None
    return wrapper


@bot.message_handler(commands=['start'])
@log_action
@error_handler
async def start_command(message):
    await BotService.send_welcome(bot, message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Видалити останню")
@log_action
async def delete(message):
    markup = keyboards.get_delete_confirmation_menu()
    await bot.send_message(message.chat.id, "Ви точно хочете видалити останній запис?", reply_markup = markup)

@bot.message_handler(func=lambda message: message.text == "Додати витрату")
@log_action
@error_handler
async def ask_for_amount(message):
    await bot.set_state(message.from_user.id, ExpenseState.amount, message.chat.id)
    await BotService.ask_amount(bot, message.chat.id)

@bot.message_handler(state=ExpenseState.amount)
async def get_amount(message):
    text_parts = message.text.split()
    amount, error_msg = Validator.parse_amount(text_parts[0])

    if error_msg:
        await bot.send_message(message.chat.id, error_msg)
        return

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["amount"] = amount
    await bot.set_state(message.from_user.id, ExpenseState.category, message.chat.id)
    search_term = text_parts[1] if len(text_parts) > 1 else ""
    suggested = await db.suggest_category(message.chat.id, search_term) if search_term else None

    markup = keyboards.get_categories_menu()
    display_text = "Обери категорію:"
    if suggested:
        display_text = f"Я думаю це **{suggested}**. Правильно? Чи обери іншу:"

    await bot.send_message(message.chat.id, display_text, reply_markup = markup, parse_mode="Markdown")

@bot.message_handler(state=ExpenseState.category)
async def save_all_data(message):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        amount = data.get("amount")
    category = message.text
    user_id = message.chat.id
    current_date = datetime.now().strftime("%Y-%m-%d")

    await db.add_expense(user_id, amount, category, current_date)
    await bot.delete_state(message.from_user.id, message.chat.id)
    today_total = await db.get_today_spending(user_id, current_date)
    total_spent = await db.get_total_spending(user_id)

    text = f"Збережено: {amount} грн, на '{category}'"
    if today_total > Config.DAILY_LIMIT:
        text += f"\n\n*Увага! Ти перевищила денний ліміт!\nСьогодні витрачено: *{today_total}* грн*"

    if total_spent > Config.MONTHLY_LIMIT:
        text += f"\n\n*ГЛОБАЛЬНИЙ ЛІМІТ!*\nЗагальна сума: {total_spent} грн.\nПора зупинитися!"
    await BotService.send_report(bot, user_id, text)

@bot.message_handler(func=lambda message: message.text == "Мої витрати")
@log_action
async def show_menu(message):
    markup = keyboards.get_period_menu()
    await bot.send_message(message.chat.id, "За який період показати звіт?", reply_markup = markup)


@bot.message_handler(func=lambda message: message.text == "Сьогодні")
@log_action
async def show_daily(message):
    data = await db.get_today_expenses(message.chat.id)
    text = reports.format_expense_report(data, "сьогодні")
    await BotService.send_report(bot, message.chat.id, text)



@bot.message_handler(func=lambda message: message.text == "Тиждень")
@log_action
async def show_weekly(message):
    data = await db.get_expenses_by_period(message.chat.id, 7)
    text = reports.format_expense_report(data, "тиждень")

    data_stats = await db.get_weekly_stats(message.chat.id)
    chart_path = reports.create_weekly_chart(data_stats, message.chat.id)

    await BotService.send_report(bot, message.chat.id, text, chart_path)


@bot.message_handler(func=lambda message: message.text == "Місяць")
@log_action
async def show_monthly(message):
    data = await db.get_expenses_by_period(message.chat.id, 30)
    text = reports.format_expense_report(data, "місяць")

    await BotService.send_report(bot, message.chat.id, text)


@bot.message_handler(func=lambda message: message.text == "Назад")
@log_action
async def back(message):
    await BotService.send_welcome(bot, message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Статистика")
@log_action
async def show_stats(message):
    stats = await db.get_expenses_by_category(message.chat.id)
    chart_path = reports.create_stats_chart(stats, message.chat.id)

    if not stats:
        await bot.send_message(message.chat.id, "Даних для статистики поки немає.")
    else:
        report = "*Витрати по категоріям:*\n"
        report += "\n".join([f"- {r[0]} | *{r[1]} грн*" for r in stats])
        await BotService.send_report(bot, message.chat.id, report, chart_path)


@bot.message_handler(func=lambda message: message.text == "Експорт в Excel")
@log_action
@error_handler
async def export_to_excel(message):
    data = await db.get_all_expenses_for_export(message.chat.id)
    file_path = reports.create_excel_report(data, message.chat.id)
    if file_path:
        with open(file_path, 'rb') as file:
            await bot.send_document(message.chat.id, file, caption="Твій повний звіт у Excel")

        os.remove(file_path)
    else:
        await bot.send_message(message.chat.id, "У базі поки немає даних для експорту.")


@bot.message_handler(func=lambda message: message.text == "Додати дохід")
@log_action
async def ask_income(message):
    await bot.send_message(message.chat.id, "Ввести суму доходу:")
    await bot.set_state(message.from_user.id, IncomeState.amount, message.chat.id)

@bot.message_handler(state=IncomeState.amount)
async def get_income_amount(message):
    amount, error_msg = Validator.parse_amount(message.text)
    if error_msg:
        await bot.send_message(message.chat.id, error_msg)
        return
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["amount"] = amount

    await bot.set_state(message.from_user.id, IncomeState.category, message.chat.id)
    markup = keyboards.get_incomes_categories_menu()
    await bot.send_message(message.chat.id, "Обери джерело:", reply_markup = markup)


@bot.message_handler(state=IncomeState.category)
async def save_income(message):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        amount = data.get("amount")
    user_id = message.chat.id
    category = message.text
    current_date = datetime.now().strftime("%Y/%m/%d")

    await db.add_income(user_id, amount, category, current_date)
    await bot.delete_state(message.from_user.id, message.chat.id)

    await bot.send_message(user_id, f"Записано +{amount} грн ({category})", reply_markup=keyboards.get_main_menu())


@bot.message_handler(func=lambda message: message.text == "Загальний баланс")
@log_action
@error_handler
async def total_balance(message):
    user_id = message.chat.id
    total_income = await db.get_total_income(message.chat.id)
    total_expenses = await db.get_total_spending(message.chat.id)
    chart_path = reports.create_balance_chart(total_income, total_expenses, user_id)
    balance_uah = total_income - total_expenses

    eur_rate = currency.get_exchange_rate("EUR")

    if eur_rate:
        balance_eur = round(balance_uah / eur_rate, 2)
        eur_text = f" (~{balance_eur} EUR)"
    else:
        eur_text = ""

    report = (f"*Твій фінансовий звіт:*\n"
              f"Доходи: {total_income} грн\n"
              f"Витрати: {total_expenses} грн\n"
              f"----------------------\n"
              f"*Залишок: {balance_uah} грн*{eur_text}")

    inline_markup = keyboards.get_balance_inline()
    with open(chart_path, 'rb') as photo:
        await bot.send_photo(message.chat.id, photo, caption=report, parse_mode="Markdown", reply_markup=inline_markup)
    import os
    os.remove(chart_path)

@bot.message_handler(func=lambda message: message.text == "Історія")
@log_action
@error_handler
async def show_history_first_page(message):
    await send_history_page(message.chat.id, page=1)

async def send_history_page(chat_id, page, message_id=None):
    limit = 5
    offset = (page - 1) * limit
    total_count = await db.get_expenses_count(chat_id)
    if total_count == 0:
        text = "Записів ще немає."
        if message_id:
            await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
        else:
            await bot.send_message(chat_id, text)
        return

    total_pages = math.ceil(total_count / limit)
    records = await db.get_expenses_page(chat_id, limit, offset)

    text = f"*Історія витрат (Сторінка {page} з {total_pages})*\n\n"
    for amount, category, date in records:
        text += f"{date}: *{amount} грн* - {category}\n"

    markup = keyboards.get_pagination_keyboard(page, total_pages)

    if message_id:
        await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="Markdown")
    else:
        await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")


@bot.message_handler(commands=["rate"])
@error_handler
@log_action
async def show_rate(message):
    eur_rate = currency.get_exchange_rate("EUR")
    usd_rate = currency.get_exchange_rate("USD")

    if eur_rate and usd_rate:
        text = (f"*Актуальний курс НБУ:*\n\n"
                f"🇪🇺 Євро:* {eur_rate} грн*\n"
                f"🇺🇸 Долар:* {usd_rate} грн*\n")
        await bot.send_message(message.chat.id, text, parse_mode="Markdown")

    else:
        await bot.send_message(message.chat.id, "Не вдалося отримати курс. Спробуй пізніше.", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
@log_action
async def handle_all_callbacks(call):
    user_id = call.message.chat.id
    if call.data == "refresh_balance":
        await bot.answer_callback_query(call.id, text="Оновлюю данні...")
        await total_balance(call.message)

    elif call.data == "confirm_delete":

        success = await db.delete_expense(call.message.chat.id)
        if success:
            new_text = "Видалено останній запис!"
        else:
            new_text = "Не вдалось знайти записів для видалення."

        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=new_text)

    elif call.data == "cancel_confirm":
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "Видалення скасовано.")

    elif call.data == "set_daily":
        await bot.answer_callback_query(call.id)
        await bot.send_message(user_id, "Введіть новий *денний* ліміт (цифрами):", parse_mode="Markdown")
        await bot.set_state(user_id, SettingsState.daily_limit, user_id)

    elif call.data == "set_monthly":
        await bot.answer_callback_query(call.id)
        await bot.send_message(user_id, "Введіть новий *місячний* ліміт (цифрами):", parse_mode="Markdown")
        await bot.set_state(user_id, SettingsState.monthly_limit, user_id)

    elif call.data.startswith("page_"):
        page = int(call.data.split("_")[1])
        await send_history_page(call.message.chat.id, page, call.message.message_id)
        await bot.answer_callback_query(call.id)

    await bot.answer_callback_query(call.id)

@bot.message_handler(state=SettingsState.daily_limit)
async def process_daily_limit_step(message):
    try:
        new_limit = float(message.text)
        user_id = message.chat.id
        await db.update_user_limit(user_id, daily = new_limit)
        await bot.send_message(user_id, f"Денний ліміт оновлено до {new_limit}!")
    except ValueError:
        await bot.send_message(message.chat.id, "Помилка! Введіть число (наприклад, 600). Спробуйте ще раз /settings")
    finally:
        await bot.delete_message(message.from_user.id, message.chat.id)

@bot.message_handler(state=SettingsState.monthly_limit)
async def process_monthly_limit_step(message):
    try:
        new_limit = float(message.text)
        user_id = message.chat.id
        await db.update_user_limit(user_id, monthly = new_limit)
        await bot.send_message(user_id, f"Місячний ліміт оновлено до {new_limit}!")
    except ValueError:
        await bot.send_message(message.chat.id, "Помилка! Введіть число. Спробуйте ще раз /settings")
    finally:
        await bot.delete_message(message.from_user.id, message.chat.id)

@bot.message_handler(commands=['settings'])
async def show_settings(message):
    user_id = message.chat.id
    settings = await db.get_user_settings(user_id)

    daily = settings["daily"]
    monthly = settings["monthly"]

    text = (
        f"*Налаштування бюджету*\n\n"
        f"Твій денний ліміт: *{daily}*\n"
        f"Твій місячний ліміт: *{monthly}*\n"
        "Що саме хочеш змінити?"
    )

    markup = types.InlineKeyboardMarkup()
    btn_daily = types.InlineKeyboardButton("Змінити денний ліміт", callback_data="set_daily")
    btn_monthly = types.InlineKeyboardButton("Змінити місячний ліміт", callback_data="set_monthly")
    markup.add(btn_daily, btn_monthly)


    await bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['about'])
async def show_about(message):
    await bot.send_message(message.chat.id, "Я бекенд проект")


@bot.message_handler(commands=['status'])
@error_handler
async def system_status(message):
    if message.chat.id != 5096558702:
        await bot.send_message(message.chat.id, "У вас немає доступу до цієї команди")
        return
    db_count = await db.get_db_status()
    py_version = platform.python_version()
    os_info = platform.system()
    status_text = (
        f"*System Health Check:*\n\n"
        f"*Бот:* Online\n"
        f"*База даних:* Connected\n"
        f"*Записів у БД:* `{db_count}`\n"
        f"*Python:* `{py_version}`\n"
        f"*ОС:* `{os_info}`\n"
        f"*Час сервера:* `{datetime.now().strftime('%H:%M:%S')}`"
    )
    await bot.send_message(message.chat.id, status_text, parse_mode="Markdown")

@bot.message_handler(commands=['dashboard'])
@error_handler
@log_action
async def send_magic_link(message):
    user_id = message.chat.id
    new_token = secrets.token_urlsafe(16)
    await db.save_token(user_id, new_token)
    magic_link = f"http://127.0.0.1:8001/dashboard/{user_id}?token={new_token}"
    text = (
        f"*Сейф відкрито*\n\n"
        f"Ось твоє персональне посилання на дашборд. "
        f"Воно дійсне, поки ти не згенеруєш нове.\n\n"
        f"[Перейти до Дашборду]({magic_link})"
    )
    await bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)



def signal_handler(_signal, _frame):
    bot.send_message(5096558702, "Бот вимикається для оновлення або технічних робіт. Скоро повернуся!")
    scheduler.shutdown()
    os._exit(0)
signal.signal(signal.SIGINT, signal_handler)


async def main():
    await db.init_db()
    scheduler.add_job(send_weekly_report,'cron', day_of_week='mon', hour=9, minute=0)
    scheduler.start()
    print("Асинхронний бот запущений!")
    await bot.infinity_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот зупинений")

