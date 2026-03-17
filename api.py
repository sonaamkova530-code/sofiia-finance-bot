from fastapi import FastAPI
from database import Database

app = FastAPI(title="Budget Bot API")
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
