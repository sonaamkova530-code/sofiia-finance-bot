from telebot import types

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Додати витрату", "Видалити останню", "Мої витрати", "Статистика", "Експорт в Excel")
    return markup

def get_categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Кава", "Обід", "Транспорт", "Шопінг")
    return markup

def get_period_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Сьогодні", "Тиждень", "Місяць", "Назад")
    return markup

