import os

import keyboards

class BotService:
    @staticmethod
    async def send_welcome(bot, chat_id):
        markup = keyboards.get_main_menu()
        await bot.send_message(chat_id, "Привітик, обери дію:", reply_markup=markup)

    @staticmethod
    async def send_report(bot, chat_id, text, photo_path=None):
        try:
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    await bot.send_photo(chat_id, photo, caption=text, parse_mode="Markdown")
                os.remove(photo_path)
            else:
                await bot.send_message(chat_id, text, parse_mode="Markdown")
        except Exception as e:
            print(f"Помилка в BotService.send_report: {e}")
            await bot.send_message(chat_id, "Сталася помилка при відправці звіту.")
        finally:
            await BotService.send_welcome(bot, chat_id)


    @staticmethod
    async def ask_amount(bot, chat_id, suggested_cat=None):
        text="Введи суму (наприклад 150.60)"
        if suggested_cat:
            text = f"Здається це *{suggested_cat}*.\nВведи суму (наприклад 150.60)"
        return await bot.send_message(chat_id, text, parse_mode="Markdown")

    @staticmethod
    async def ask_category(bot, chat_id, markup):
        return await bot.send_message(chat_id, "Обери категорію:", reply_markup=markup)




