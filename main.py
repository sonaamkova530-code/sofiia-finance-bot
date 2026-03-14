import keyboards
import currency
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
    markup = keyboards.get_delete_confirmation_menu()
    bot.send_message(message.chat.id, "Ви точно хочете видалити останній запис?", reply_markup = markup)


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

@bot.callback_query_handler(func=lambda call: call.data == "refresh_balance")
def refresh_balance_callback(call):
    bot.answer_callback_query(call.id, text="Оновлюю данні...")

    total_balance(call.message)


@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
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

    bot.answer_callback_query(call.id)


bot.infinity_polling()