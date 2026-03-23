from telebot.asyncio_handler_backends import StatesGroup, State

class ExpenseState(StatesGroup):
    amount = State()
    category = State()

class IncomeState(StatesGroup):
    amount = State()
    category = State()

class SettingsState(StatesGroup):
    daily_limit = State()
    monthly_limit = State()