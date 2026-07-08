from fastapi import FastAPI, Request, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from database import Database
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_cache.decorator import cache
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis = aioredis.from_url("redis://127.0.0.1:6379", encoding="utf-8")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    print("Redis успішно підключено через lifespan!")
    yield
    print("Сервер зупинено")


app = FastAPI(title="Budget Bot API", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
db = Database("my_budget.db")


@app.get("/")
async def home():
    return {"message": "Привітик, API працює"}


@app.get("/expenses/{user_id}")
async def get_expenses(user_id: int):
    raw_data = await db.get_user_expenses(user_id)
    formatted_data = []
    for row in raw_data:
        formatted_data.append({
            "amount": row[0],
            "category": row[1],
            "date": row[2],
        })

    return {
        "user_id": user_id,
        "count": len(formatted_data),
        "expenses": formatted_data
    }


@app.get("/analytics/{user_id}")
@cache(expire=60)
async def get_analytics(request: Request, user_id: int):
    print(f"🚨 УВАГА! РОБИМО ВАЖКИЙ ЗАПИТ У БАЗУ ДАНИХ ДЛЯ {user_id} 🚨")
    stats = await db.get_expenses_by_category(user_id)
    breakdown = {category: amount for category, amount in stats}
    return {
        "status": "success",
        "user_id": user_id,
        "analytics": breakdown
    }


@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
async def get_dashboard(request: Request, user_id: int, token: str = None):
    valid_token = await db.get_token(user_id)
    if not token or token != valid_token:
        raise HTTPException(status_code=403, detail="Доступ заборонено! Згенеруй нове посилання через бота.")

    raw_data = await db.get_user_expenses(user_id)
    total_sum = sum([row[0] for row in raw_data])
    cat_stats = await db.get_expenses_by_category(user_id)
    labels = [row[0] for row in cat_stats]
    values = [row[1] for row in cat_stats]
    count = len(raw_data)
    expenses_list = []
    for row in raw_data:
        expenses_list.append({
            "amount": row[0],
            "category": row[1],
            "date": row[2],
        })

    limit = 3000
    status = "В нормі"
    status_color = "#e8f0fe"
    if total_sum > limit:
        status = "Перевищення!"
        status_color = "#fce8e6"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "chart_labels": labels,
        "chart_values": values,
        "user_id": user_id,
        "expenses": expenses_list,
        "total": total_sum,
        "count": count,
        "status": status,
        "status_color": status_color,
    })
