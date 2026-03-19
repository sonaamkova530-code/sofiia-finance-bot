import keyboards
import functools
import currency
import os
from dotenv import load_dotenv
import telebot
import reports
from database import Database
from datetime import datetime
import logging
from bot_service import BotService
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
db = Database(Config.DB_NAME)
bot = telebot.TeleBot(Config.TOKEN)

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



def log_action(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"--- [LOG] Виклик функції: {func.__name__} ---")
        result = func(*args, **kwargs)
        print(f"--- [LOG] Функція {func.__name__} завершена ---")
        return result
    return wrapper

def error_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR] Помилка у функції {func.__name__}: {e}")
            return None
    return wrapper


@bot.message_handler(commands=['start'])
@log_action
@error_handler
def start_command(message):
    BotService.send_welcome(bot, message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Видалити останню")
@log_action
def delete(message):
    markup = keyboards.get_delete_confirmation_menu()
    bot.send_message(message.chat.id, "Ви точно хочете видалити останній запис?", reply_markup = markup)

@bot.message_handler(func=lambda message: message.text == "Додати витрату")
@log_action
@error_handler
def ask_for_amount(message):
    msg = BotService.ask_amount(bot, message.chat.id)
    bot.register_next_step_handler(msg, get_amount)

def get_amount(message):
    amount, error_msg = Validator.parse_amount(message.text)

    if error_msg:
        bot.send_message(message.chat.id, error_msg)
        return
    markup = keyboards.get_categories_menu()
    msg = BotService.ask_category(bot, message.chat.id, markup)

    bot.register_next_step_handler(msg, lambda m: save_all_data(m, amount))


def save_all_data(message, amount):
    category = message.text
    user_id = message.chat.id

    current_date = datetime.now().strftime("%Y-%m-%d")

    db.add_expense(message.chat.id, amount, category, current_date)

    text = f"Збережено: {amount} грн, на '{category}'"
    today_total = db.get_today_spending(user_id, current_date)
    if today_total > Config.DAILY_LIMIT:
        text += f"\n\n*Увага! Ти перевищила денний ліміт!\nСьогодні витрачено: *{today_total}* грн*"
    total_spent = db.get_total_spending(user_id)
    if total_spent > Config.MONTHLY_LIMIT:
        text += f"\n\n*ГЛОБАЛЬНИЙ ЛІМІТ!*\nЗагальна сума: {total_spent} грн.\nПора зупинитися!"
    BotService.send_report(bot, user_id, text)


@bot.message_handler(func=lambda message: message.text == "Мої витрати")
@log_action
def show_menu(message):
    markup = keyboards.get_period_menu()
    bot.send_message(message.chat.id, "За який період показати звіт?", reply_markup = markup)


@bot.message_handler(func=lambda message: message.text == "Сьогодні")
@log_action
def show_daily(message):
    data = db.get_today_expenses(message.chat.id)
    text = reports.format_expense_report(data, "сьогодні")
    BotService.send_report(bot, message.chat.id, text)



@bot.message_handler(func=lambda message: message.text == "Тиждень")
@log_action
def show_weekly(message):
    data = db.get_expenses_by_period(message.chat.id, 7)
    text = reports.format_expense_report(data, "тиждень")

    data_stats = db.get_weekly_stats(message.chat.id)
    chart_path = reports.create_weekly_chart(data_stats, message.chat.id)

    BotService.send_report(bot, message.chat.id, text, chart_path)


@bot.message_handler(func=lambda message: message.text == "Місяць")
@log_action
def show_monthly(message):
    data = db.get_expenses_by_period(message.chat.id, 30)
    text = reports.format_expense_report(data, "місяць")

    BotService.send_report(bot, message.chat.id, text)


@bot.message_handler(func=lambda message: message.text == "Назад")
@log_action
def back(message):
    BotService.send_welcome(bot, message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Статистика")
@log_action
def show_stats(message):
    stats = db.get_expenses_by_category(message.chat.id)
    chart_path = reports.create_stats_chart(stats, message.chat.id)

    if not stats:
        bot.send_message(message.chat.id, "Даних для статистики поки немає.")
    else:
        report = "*Витрати по категоріям:*\n"
        report += "\n".join([f"- {r[0]} | *{r[1]} грн*" for r in stats])
        BotService.send_report(bot, message.chat.id, report, chart_path)


@bot.message_handler(func=lambda message: message.text == "Експорт в Excel")
@log_action
@error_handler
def export_to_excel(message):
    data = db.get_all_expenses_for_export(message.chat.id)
    file_path = reports.create_excel_report(data, message.chat.id)
    if file_path:
        with open(file_path, 'rb') as file:
            bot.send_document(message.chat.id, file, caption="Твій повний звіт у Excel")

        os.remove(file_path)
    else:
        bot.send_message(message.chat.id, "У базі поки немає даних для експорту.")


@bot.message_handler(func=lambda message: message.text == "Додати дохід")
@log_action
def ask_income(message):
    msg = bot.send_message(message.chat.id, "Ввести суму доходу:")
    bot.register_next_step_handler(msg, get_income_amount)

def get_income_amount(message):
    amount, error_msg = Validator.parse_amount(message.text)
    if error_msg:
        bot.send_message(message.chat.id, error_msg)
        return

    markup = keyboards.get_incomes_categories_menu()
    msg = bot.send_message(message.chat.id, "Обери джерело:", reply_markup = markup)
    bot.register_next_step_handler(msg, lambda m: save_income(m, amount))


def save_income(message, amount):
    category = message.text
    current_date = datetime.now().strftime("%Y/%m/%d")
    db.add_income(message.chat.id, amount, category, current_date)
    bot.send_message(message.chat.id, f"Записано +{amount} грн ({category})", reply_markup=keyboards.get_main_menu())


@bot.message_handler(func=lambda message: message.text == "Загальний баланс")
@log_action
@error_handler
def total_balance(message):
    user_id = message.chat.id
    total_income = db.get_total_income(message.chat.id)
    total_expenses = db.get_total_spending(message.chat.id)
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
        bot.send_photo(message.chat.id, photo, caption=report, parse_mode="Markdown", reply_markup=inline_markup)
    import os
    os.remove(chart_path)


@bot.message_handler(commands=["rate"])
@error_handler
@log_action
def show_rate(message):
    eur_rate = currency.get_exchange_rate("EUR")
    usd_rate = currency.get_exchange_rate("USD")

    if eur_rate and usd_rate:
        text = (f"*Актуальний курс НБУ:*\n\n"
                f"🇪🇺 Євро:* {eur_rate} грн*\n"
                f"🇺🇸 Долар:* {usd_rate} грн*\n")
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    else:
        bot.send_message(message.chat.id, "Не вдалося отримати курс. Спробуй пізніше.", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
@log_action
def handle_all_callbacks(call):
    user_id = call.message.chat.id

    if call.data == "refresh_balance":
        bot.answer_callback_query(call.id, text="Оновлюю данні...")
        total_balance(call.message)

    elif call.data == "confirm_delete":

        success = db.delete_expense(call.message.chat.id)
        if success:
            new_text = "Видалено останній запис!"
        else:
            new_text = "Не вдалось знайти записів для видалення."

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=new_text)

    elif call.data == "cancel_confirm":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "Видалення скасовано.")

    elif call.data == "set_daily":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(user_id, "Введіть новий **денний** ліміт (цифрами):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_daily_limit_step)

    elif call.data == "set_monthly":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(user_id, "Введіть новий **місячний** ліміт (цифрами):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_monthly_limit_step)

    bot.answer_callback_query(call.id)

def process_daily_limit_step(message):
    try:
        new_limit = float(message.text)
        user_id = message.chat.id
        db.update_user_limit(user_id, daily = new_limit)
        bot.send_message(user_id, f"Денний ліміт оновлено до {new_limit}!")
    except ValueError:
        bot.send_message(message.chat.id, "Помилка! Введіть число (наприклад, 600). Спробуйте ще раз /settings")

def process_monthly_limit_step(message):
    try:
        new_limit = float(message.text)
        user_id = message.chat.id
        db.update_user_limit(user_id, monthly = new_limit)
        bot.send_message(user_id, f"Місячний ліміт оновлено до {new_limit}!")
    except ValueError:
        bot.send_message(message.chat.id, "Помилка! Введіть число. Спробуйте ще раз /settings")


@bot.message_handler(commands=['settings'])
def show_settings(message):
    user_id = message.chat.id
    settings = db.get_user_settings(user_id)

    daily = settings["daily"]
    monthly = settings["monthly"]

    text = (
        f"**Налаштування бюджету**\n\n"
        f"Твій денний ліміт: **{daily}**\n"
        f"Твій місячний ліміт: **{monthly}**\n"
        "Що саме хочеш змінити?"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    btn_daily = telebot.types.InlineKeyboardButton("Змінити денний ліміт", callback_data="set_daily")
    btn_monthly = telebot.types.InlineKeyboardButton("Змінити місячний ліміт", callback_data="set_monthly")
    markup.add(btn_daily, btn_monthly)


    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")




if __name__ == "__main__":
    bot.infinity_polling()