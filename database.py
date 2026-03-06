import sqlite3

class Database:
    def __init__(self, db_file):
        # Підключаємося до файлу бази даних
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        # Твій вивчений SQL у дії! Створюємо таблицю витрат
        with self.connection:
            return self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    category TEXT,
                    date TEXT
                )
            """)

    def add_expense(self, user_id, amount, category, date):
        # Команда INSERT для додавання даних
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                (user_id, amount, category, date)
            )

    def delete_expense(self, user_id):
        self.cursor.execute("SELECT id FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        last_id = self.cursor.fetchone()
        if last_id:
            self.cursor.execute("DELETE FROM expenses WHERE id = ?", (last_id[0],))
            self.connection.commit()
            return True
        return False

    def get_user_expenses(self, user_id):
        # Команда SELECT для звіту
        with self.connection:
            return self.cursor.execute(
                "SELECT amount, category, date FROM expenses WHERE user_id = ?",
                (user_id,)
            ).fetchall()

    def get_total_spending(self, user_id):
        self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_today_spending(self, user_id, date):
        self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date = ?", (user_id, date))
        result = self.cursor.fetchone()
        return result[0] if result is not None else 0


    def get_expenses_by_period(self, user_id, days):
        query = f"SELECT amount, category, date FROM expenses WHERE user_id = ? AND date >= DATE('now', '-{days} days')"
        self.cursor.execute(query,(user_id,))
        return self.cursor.fetchall()

    def get_today_expenses(self, user_id):
        query = f"SELECT amount, category, date FROM expenses WHERE user_id = ? AND date = date('now')"
        self.cursor.execute(query,(user_id,))
        return self.cursor.fetchall()

    def get_expenses_by_category(self, user_id):
        self.cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC""", (user_id,))
        return self.cursor.fetchall()

    def get_all_expenses_for_export(self, user_id):
        self.cursor.execute("SELECT amount, category, date FROM expenses WHERE user_id = ? ORDER BY date DESC", (user_id,))
        return self.cursor.fetchall()
