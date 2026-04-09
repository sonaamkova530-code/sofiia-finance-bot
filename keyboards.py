from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_incomes_categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Зарплата", "Подарунок", "Кешбек", "Інше")
    return markup


def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Додати витрату", "Додати дохід")
    markup.row("Мої витрати", "Статистика")
    markup.row("Експорт в Excel", "Загальний баланс")
    markup.row("Видалити останню", "Історія")
    return markup


def get_categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Кава", "Обід", "Транспорт", "Шопінг")
    return markup


def get_period_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Сьогодні", "Тиждень", "Місяць", "Назад")
    return markup


def get_balance_inline():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Оновити курс", callback_data="refresh_balance"))
    return markup


def get_history_keyboard(current_page, total_pages, records):
    markup = InlineKeyboardMarkup()

    for index, record in enumerate(records, start=1):
        record_id = record[0]

        btn_edit = InlineKeyboardButton(f"Виправити №{index}", callback_data=f"edit_exp_{record_id}_{current_page}")
        btn_del = InlineKeyboardButton(f"Видалити №{index}", callback_data=f"del_exp_{record_id}_{current_page}")
        markup.row(btn_edit, btn_del)

    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton("Назад", callback_data=f"page_{current_page - 1}"))

    if current_page < total_pages:
        buttons.append(InlineKeyboardButton("Вперед", callback_data=f"page_{current_page + 1}"))

    if buttons:
        markup.add(*buttons)
    return markup


def get_delete_confirmation_menu():
    markup = InlineKeyboardMarkup()
    btn_yes = InlineKeyboardButton("Так, видалити", callback_data="confirm_delete")
    btn_no = InlineKeyboardButton("Ні, залишити", callback_data="cancel_confirm")
    markup.add(btn_yes, btn_no)
    return markup
