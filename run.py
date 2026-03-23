import asyncio
import uvicorn
from main import main as run_bot_logic
from api import app as fastapi_app


async def run_api():
    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def start_everything():
    print("Запускаємо Бот та API")
    await asyncio.gather(
        run_bot_logic(),
        run_api()
    )


if __name__ == "__main__":
    try:
        asyncio.run(start_everything())
    except KeyboardInterrupt:
        print("\nПроцеси зупинено користувачем.")








