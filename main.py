import os
from dotenv import load_dotenv
import telebot
from telebot import types
from database import Database
from datetime import datetime
load_dotenv()
db = Database('my_budget.db')
bot = telebot.TeleBot(os.getenv("TOKEN"))


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Додати витрату")
    btn2 = types.KeyboardButton("Видалити останню")
    btn3 = types.KeyboardButton("Мої витрати")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Привітик, обери дію:", reply_markup = markup)

@bot.message_handler(func=lambda message: message.text == "Додати витрату")
def ask(message):
    msg = bot.send_message(message.chat.id, "Введи суму (наприклад 150.5)")
    bot.register_next_step_handler(msg, get_amount)


def get_amount(message):
    try:
        amount = float(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Кава","Обід","Транспорт","Шопінг")
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

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Додати витрату", "Видалити останню", "Мої витрати")
    bot.send_message(user_id, f"Збережено: {amount} грн, на '{category}'", reply_markup = markup)
    today_total = db.get_today_spending(user_id, current_date)
    if today_total > DAILY_LIMIT:
        bot.send_message(user_id, f"*Увага! Ти перевищила денний ліміт!\nСьогодні витрачено: *{today_total}* грн*", parse_mode = "Markdown")


@bot.message_handler(func=lambda message: message.text == "Видалити останню")
def delete(message):
    db.delete_expense(message.chat.id)
    bot.send_message(message.chat.id, "Видалено останній запис!")

@bot.message_handler(func=lambda message: message.text == "Мої витрати")
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Сьогодні")
    btn2 = types.KeyboardButton("Тиждень")
    btn3 = types.KeyboardButton("Місяць")
    btn4 = types.KeyboardButton("Назад")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, "За який період показати звіт?", reply_markup = markup)


@bot.message_handler(func=lambda message: message.text == "Сьогодні")
def show_daily(message):
    data = db.get_expenses_by_period(message.chat.id, 0)
    if not data:
        bot.send_message(message.chat.id, "За сьогодні витрат немає.")
        start(message)
    else:
        total = sum(r[0] for r in data)
        report = "*Витрати за сьогодні:*\n" + "\n".join([f"- {r[0]} грн | ({r[1]})" for r in data])
        report += f"*\nВсього за сьогодні: {total} грн*"
        bot.send_message(message.chat.id, report, parse_mode="Markdown")
        start(message)



@bot.message_handler(func=lambda message: message.text == "Тиждень")
def show_weekly(message):
    data = db.get_expenses_by_period(message.chat.id, 7)
    if not data:
        bot.send_message(message.chat.id, "За останній тиждень витрат немає.")
        start(message)
    else:
        total = sum(r[0] for r in data)
        report = "*Витрати за тиждень:*\n" + "\n".join([f"- {r[0]} грн | ({r[1]})" for r in data])
        report += f"*\nВсього за тиждень: {total} грн*"
        bot.send_message(message.chat.id, report, parse_mode="Markdown")
        start(message)


@bot.message_handler(func=lambda message: message.text == "Місяць")
def show_monthly(message):
    data = db.get_expenses_by_period(message.chat.id, 30)
    if not data:
        bot.send_message(message.chat.id, "За останній місяць витрат немає.")
        start(message)
    else:
        total = sum(r[0] for r in data)
        report = "*Витрати за місяць:*\n" + "\n".join([f"- {r[0]} грн | ({r[1]})" for r in data])
        report += f"*\nВсього за місяць: {total} грн*"
        bot.send_message(message.chat.id, report, parse_mode="Markdown")
        start(message)


@bot.message_handler(func=lambda message: message.text == "Назад")
def back(message):
    start(message)


bot.infinity_polling()
