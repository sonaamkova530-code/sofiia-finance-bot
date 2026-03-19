from fastapi import FastAPI
from database import Database
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

app = FastAPI(title="Budget Bot API")
templates = Jinja2Templates(directory="templates")
db = Database("my_budget.db")

@app.get("/")
def home():
    return {"message": "Привітик, API працює"}

@app.get("/expenses/{user_id}")
def get_expenses(user_id: int):
    raw_data = db.get_user_expenses(user_id)

    formatted_data = []
    for row in raw_data:
        formatted_data.append({
            "amount": row[0],
            "category": row[1],
            "date": row[2],
        })

    return {
        "user_id": user_id,
        "count" : len(formatted_data),
        "expenses" : formatted_data
    }
@app.get("/analytics/{user_id}")
def get_analytics(user_id: int):
    stats = db.get_expenses_by_category(user_id)
    breakdown = {category: amount for category, amount in stats}
    return {
        "status": "success",
        "user_id": user_id,
        "analytics": breakdown
    }

@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
def get_dashboard(request: Request, user_id: int):
    raw_data = db.get_user_expenses(user_id)
    total_sum = sum([row[0] for row in raw_data])
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

    return templates.TemplateResponse("index.html",{
        "request": request,
        "user_id": user_id,
        "expenses": expenses_list,
        "total": total_sum,
        "count": count,
        "status": status,
        "status_color": status_color,
    })