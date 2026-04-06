import time
from  telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate

class AntispamMiddleware(BaseMiddleware):
    def __init__(self, limit=1.0):
        super().__init__()
        self.limit = limit
        self.last_action_time = {}
        self.update_types = ["message", "callback_query"]

    async def pre_process(self, message, data):
        user_id = message.from_user.id
        current_time = time.time()

        if user_id in self.last_action_time:
            time_passed = current_time - self.last_action_time[user_id]

            if time_passed < self.limit:
                print(f"[ANTISPAM] заблоковано спам від {user_id}!")
                return CancelUpdate()
        self.last_action_time[user_id] = current_time
        return None

    async def post_process(self, message, data, exception):
        pass