import threading
import uvicorn
from main import bot
from api import app

def run_bot():
    print("Бот запускається...")
    bot.infinity_polling()

def run_api():
    print("API запускається...")
    uvicorn.run(app, host="127.0.0.1", port=8001)

if __name__ == "__main__":
    bot.thread = threading.Thread(target=run_bot, daemon=True)
    bot.thread.start()
    run_api()