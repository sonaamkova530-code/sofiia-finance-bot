import sqlite3

class Database:
    def __init__(self, db_file):
        # Підключаємося до файлу бази даних
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()
        self.create_settings_table()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            date TEXT)""")
        self.connection.commit()


    def add_income(self, user_id, amount, category, date):
        self.cursor.execute("""INSERT INTO incomes (user_id, amount, category, date) VALUES (?, ?, ?, ?)""",
                            (user_id, amount, category, date))
        self.connection.commit()


    def get_total_income(self, user_id):
        self.cursor.execute("SELECT SUM(amount) FROM incomes WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result[0] else 0



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
        return result[0] if result[0] is not None else 0


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


    def get_weekly_stats(self, user_id):
        query = """SELECT date, SUM(amount)
        FROM expenses
        WHERE user_id = ? AND date >= DATE('now', '-7 days')
        GROUP BY date
        ORDER BY date ASC"""
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()

    def create_settings_table(self):
        query = """CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        daily_limit REAL DEFAULT 500.0,
        monthly_limit REAL DEFAULT 5000.0)"""
        self.cursor.execute(query)

    def update_user_limit(self, user_id, daily=None, monthly=None):
        if daily is not None:
            query = "INSERT INTO settings (user_id, daily_limit) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET daily_limit=?"
            self.cursor.execute(query, (user_id, daily, daily))
        if monthly is not None:
            query = "INSERT INTO settings (user_id, monthly_limit) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET monthly_limit=?"
            self.cursor.execute(query, (user_id, monthly, monthly))

        self.connection.commit()

    def get_user_settings(self, user_id):
        self.cursor.execute("SELECT daily_limit, monthly_limit FROM settings WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            return {"daily": result[0], "monthly": result[1]}
        return {"daily": 500.0, "monthly": 5000.0}

    def get_last_week(self, user_id):
        query = ("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date BETWEEN DATE('now', '-14 days') AND DATE ('now', '-8 days')")
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def suggest_category(self,user_id, text):
        query = ("SELECT category FROM expenses WHERE user_id = ? AND (category LIKE ? OR ? LIKE '%' || category || '%') ORDER BY id DESC LIMIT 1")
        search_text = f'%{text}%'
        self.cursor.execute(query, (user_id, search_text, text))
        result = self.cursor.fetchall()
        return result[0] if result else None
    def get_db_status(self):
        self.cursor.execute("SELECT COUNT(*) FROM expenses")
        count = self.cursor.fetchone()[0]
        return count


