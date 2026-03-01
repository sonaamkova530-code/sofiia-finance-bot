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
    btn1 = types.KeyboardButton("Додати витрату.")
    btn2 = types.KeyboardButton("Видалити останню.")
    btn3 = types.KeyboardButton("Мої витрати.")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Привітик, обери дію:", reply_markup = markup)

@bot.message_handler(func=lambda message: message.text == "Додати витрату.")
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


def save_all_data(message, amount):
    category = message.text
    user_id = message.chat.id

    current_date = datetime.now().strftime("%Y-%m-%d")

    db.add_expense(message.chat.id, amount, category, current_date)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Додати витрату.", "Видалити останню.", "Мої витрати.")
    bot.send_message(user_id, f"Збережено: {amount} грн, на '{category}'", reply_markup = markup)


@bot.message_handler(func=lambda message: message.text == "Видалити останню.")
def delete(message):
    db.delete_expense(message.chat.id)
    bot.send_message(message.chat.id, "Видалено останній запис!")

@bot.message_handler(func=lambda message: message.text == "Мої витрати.")
def show(message):
    data = db.get_user_expenses(message.chat.id)
    if not data:
        bot.send_message(message.chat.id, "У базі поки порожньо.")
    else:
        report = "Твої витрати:\n" + "\n".join([f"- {r[0]} грн | ({r[1]}) | ({r[2]})" for r in data])
        bot.send_message(message.chat.id, report)

bot.infinity_polling()
