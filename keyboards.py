from telebot import types

def get_incomes_categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Зарплата", "Подарунок", "Кешбек", "Інше")
    return markup


def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Додати витрату", "Додати дохід")
    markup.row("Мої витрати", "Статистика")
    markup.row("Експорт в Excel", "Загальний баланс")
    markup.row("Видалити останню")
    return markup

def get_categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Кава", "Обід", "Транспорт", "Шопінг")
    return markup

def get_period_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Сьогодні", "Тиждень", "Місяць", "Назад")
    return markup
