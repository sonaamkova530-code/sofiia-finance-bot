from fastapi import FastAPI
from database import Database

app = FastAPI(title="Budget Bot API")
db = Database("my_budget.db")

@app.get("/")
def home():
    return {"message": "Привітик, API працює"}

app.get("/expenses/{user_id}")
def get_expenses(user_id):
    raw_data = db.get_user_expenses(user_id)

    formated_data = []
    for row in raw_data:
        formated_data.append({
            "amount": row[0],
            "category": row[1],
            "date": row[2],
        })

    return {
        "user_id": user_id,
        "count" : len(formated_data),
        "date" : formated_data
    }
