import os

import keyboards

class BotService:
    @staticmethod
    def send_welcome(bot, chat_id):
        markup = keyboards.get_main_menu()
        bot.send_message(chat_id, "Привітик, обери дію:", reply_markup=markup)

    @staticmethod
    def send_report(bot, chat_id, text, photo_path=None):
        try:
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=text, parse_mode="Markdown")
                os.remove(photo_path)
            else:
                bot.send_message(chat_id, text, parse_mode="Markdown")
        except Exception as e:
            print(f"Помилка в BotService.send_report: {e}")
            bot.send_message(chat_id, "Сталася помилка при відправці звіту.")
        finally:
            BotService.send_welcome(bot, chat_id)


    @staticmethod
    def ask_amount(bot, chat_id, text="Введи суму (наприклад 150.60)"):
        return bot.send_message(chat_id, text)

    @staticmethod
    def ask_category(bot, chat_id, markup):
        return bot.send_message(chat_id, "Обери категорію:", reply_markup=markup)




