from unicodedata import category
import keyboards
import os
from dotenv import load_dotenv
import telebot
import reports
from database import Database
from datetime import datetime
import logging
logging.basicConfig(
level=logging.INFO,
filename='bot.log',
filemode='a',
format = '%(asctime)s - %(levelname)s - %(message)s',)
load_dotenv()
db = Database('my_budget.db')
bot = telebot.TeleBot(os.getenv("TOKEN"))


@bot.message_handler(commands=['start'])
def start(message):
    markup = keyboards.get_main_menu()
    bot.send_message(message.chat.id, "Привітик, обери дію:", reply_markup = markup)

@bot.message_handler(func=lambda message: message.text == "Додати витрату")
def ask(message):
    msg = bot.send_message(message.chat.id, "Введи суму (наприклад 150.5)")
    bot.register_next_step_handler(msg, get_amount)


def get_amount(message):
    try:
        amount = float(message.text)
        if amount < 0:
            bot.send_message(message.chat.id, "Сума має бути більшою за нуль!")
            return
        markup = keyboards.get_categories_menu()
        msg = bot.send_message(message.chat.id, "Обери категорію:", reply_markup = markup)
        bot.register_next_step_handler(msg, lambda m: save_all_data(m, amount))
    except ValueError:
        bot.send_message(message.chat.id, "Помилка! Треба ввести число цифрами!")

DAILY_LIMIT = 500
def save_all_data(message, amount):
    category = message.text
    user_id = message.chat.id

    current_date = datetime.now().strftime("%Y-%m-%d")

    db.add_expense(message.chat.id, amount, category, current_date)

    markup = keyboards.get_main_menu()
    bot.send_message(user_id, f"Збережено: {amount} грн, на '{category}'", reply_markup = markup)
    today_total = db.get_today_spending(user_id, current_date)
    if today_total > DAILY_LIMIT:
        bot.send_message(user_id, f"*Увага! Ти перевищила денний ліміт!\nСьогодні витрачено: *{today_total}* грн*", parse_mode = "Markdown")


@bot.message_handler(func=lambda message: message.text == "Видалити останню")
def delete(message):
    success = db.delete_expense(message.chat.id)
    if success:
        bot.send_message(message.chat.id, "Видалено останній запис!")
    else:
        bot.send_message(message.chat.id, "У базі поки порожньо, видаляти нічого.")


@bot.message_handler(func=lambda message: message.text == "Мої витрати")
def show_menu(message):
    markup = keyboards.get_period_menu()
    bot.send_message(message.chat.id, "За який період показати звіт?", reply_markup = markup)


@bot.message_handler(func=lambda message: message.text == "Сьогодні")
def show_daily(message):
    data = db.get_today_expenses(message.chat.id)
    text = reports.format_expense_report(data, "сьогодні")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    start(message)



@bot.message_handler(func=lambda message: message.text == "Тиждень")
def show_weekly(message):
    data = db.get_expenses_by_period(message.chat.id, 7)
    text = reports.format_expense_report(data, "тиждень")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    start(message)


@bot.message_handler(func=lambda message: message.text == "Місяць")
def show_monthly(message):
    data = db.get_expenses_by_period(message.chat.id, 30)
    text = reports.format_expense_report(data, "місяць")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    start(message)


@bot.message_handler(func=lambda message: message.text == "Назад")
def back(message):
    start(message)


@bot.message_handler(func=lambda message: message.text == "Статистика")
def show_stats(message):
    stats = db.get_expenses_by_category(message.chat.id)
    chart_path = reports.create_stats_chart(stats, message.chat.id)

    if chart_path:
        with open(chart_path, 'rb') as file:
            bot.send_photo(message.chat.id, file, caption="Твоя статистика у графіках:")
        import os
        os.remove(chart_path)

    if not stats:
        bot.send_message(message.chat.id, "Даних для статистики поки немає.")
    else:
        report = "*Витрати по категоріям:*\n"
        report += "\n".join([f"- {r[0]} | *{r[1]} грн*" for r in stats])
        bot.send_message(message.chat.id, report, parse_mode="Markdown")
        start(message)


@bot.message_handler(func=lambda message: message.text == "Експорт в Excel")
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

def ask_income(message):
    msg = bot.send_message(message.chat.id, "Ввести суму доходу:")
    bot.register_next_step_handler(msg, get_income_amount)

def get_income_amount(message):
    try:
        amount = float(message.text)
        markup = keyboards.get_incomes_categories_menu()
        msg = bot.send_message(message.chat.id, "Обери джерело:", reply_markup = markup)
        bot.register_next_step_handler(msg, lambda m: save_income(m, amount))
    except ValueError:
        bot.send_message(message.chat.id, "Будь ласка, введи число!")

def save_income(message, amount):
    category = message.text
    current_date = datetime.now().strftime("%Y/%m/%d")
    db.add_income(message.chat.id, amount, category, current_date)
    bot.send_message(message.chat.id, f"Записано +{amount} грн ({category})", reply_markup=keyboards.get_main_menu())


@bot.message_handler(func=lambda message: message.text == "Загальний баланс")

def total_balance(message):
    user_id = message.chat.id
    total_income = db.get_total_income(message.chat.id)
    total_expenses = db.get_total_spending(message.chat.id)
    chart_path = reports.create_balance_chart(total_income, total_expenses, user_id)

    balance = total_income - total_expenses
    report = (f"*Твій фінансовий звіт:*\n"
              f"Доходи: {total_income} грн\n"
              f"Витрати: {total_expenses} грн\n"
              f"----------------------\n"
              f"*Залишок: {balance} грн*")
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

    with open(chart_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption=report, parse_mode="Markdown")
    import os
    os.remove(chart_path)

bot.infinity_polling()
