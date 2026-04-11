import aiosqlite


class Database:
    def __init__(self, db_file):
        self.db_file = db_file

    async def _execute(self, query, params=()):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(query, params) as cursor:
                results = await cursor.fetchall()
                await db.commit()
                return results

    async def init_db(self):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    category TEXT,
                    date TEXT)
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS incomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category TEXT,
                date TEXT)
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    daily_limit REAL DEFAULT 500.0,
                    monthly_limit REAL DEFAULT 5000.0,
                    primary_currency TEXT DEFAULT 'UAH')
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    user_id INTEGER PRIMARY KEY,
                    token TEXT)
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    UNIQUE (user_id, name))
            """)

            await db.commit()

    async def get_total_income(self, user_id):
        result = await self._execute("SELECT SUM(amount) FROM incomes WHERE user_id = ?", (user_id,))
        return result[0][0] if result and result[0][0] is not None else 0

    async def add_income(self, user_id, amount, category, date):
        query = "INSERT INTO incomes (user_id, amount, category, date) VALUES (?, ?, ?, ?)"
        await self._execute(query, (user_id, amount, category, date))

    async def add_expense(self, user_id, amount, category, date):
        query = "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)"
        await self._execute(query, (user_id, amount, category, date))

    async def delete_expense(self, user_id):
        find_query = "SELECT id FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1"
        result = await self._execute(find_query, (user_id,))
        if result:
            last_id = result[0][0]
            delete_query = "DELETE FROM expenses WHERE id = ?"
            await self._execute(delete_query, (last_id,))
            return True
        return False

    async def get_user_expenses(self, user_id):
        query = "SELECT amount, category, date FROM expenses WHERE user_id = ?"
        result = await self._execute(query, (user_id,))
        return result

    async def get_total_spending(self, user_id):
        query = "SELECT SUM(amount) FROM expenses WHERE user_id = ?"
        result = await self._execute(query, (user_id,))
        return result[0][0] if result[0][0] is not None else 0

    async def get_today_spending(self, user_id, date):
        query = "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date = ?"
        result = await self._execute(query, (user_id, date))
        return result[0][0] if result[0][0] is not None else 0

    async def get_expenses_by_period(self, user_id, days):
        query = "SELECT amount, category, date FROM expenses WHERE user_id = ? AND date >= DATE('now', ?)"
        time_modifier = f"-{days} days"
        return await self._execute(query, (user_id, time_modifier))

    async def get_today_expenses(self, user_id):
        query = f"SELECT amount, category, date FROM expenses WHERE user_id = ? AND date = date('now')"
        return await self._execute(query, (user_id,))

    async def get_expenses_by_category(self, user_id):
        query = f"SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC"
        return await self._execute(query, (user_id,))

    async def get_all_expenses_for_export(self, user_id):
        query = "SELECT amount, category, date FROM expenses WHERE user_id = ? ORDER BY date DESC"
        return await self._execute(query, (user_id,))

    async def get_weekly_stats(self, user_id):
        query = "SELECT date, SUM(amount) FROM expenses WHERE user_id = ? AND date >= DATE('now', '-7 days') GROUP BY date ORDER BY date ASC"
        return await self._execute(query, (user_id,))

    async def update_user_limit(self, user_id, daily=None, monthly=None):
        if daily is not None:
            query = "INSERT INTO settings (user_id, daily_limit) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET daily_limit=?"
            await self._execute(query, (user_id, daily, daily))
        if monthly is not None:
            query = "INSERT INTO settings (user_id, monthly_limit) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET monthly_limit=?"
            await self._execute(query, (user_id, monthly, monthly))

    async def get_user_settings(self, user_id):
        result = await self._execute("SELECT daily_limit, monthly_limit FROM settings WHERE user_id = ?", (user_id,))
        if result:
            return {"daily": result[0][0], "monthly": result[0][1]}
        return {"daily": 500.0, "monthly": 5000.0}

    async def get_last_week(self, user_id):
        query = "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date BETWEEN DATE('now', '-14 days') AND DATE ('now', '-8 days')"
        result = await self._execute(query, (user_id,))
        return result[0][0] if result[0][0] is not None else 0

    async def suggest_category(self, user_id, text):
        query = "SELECT category FROM expenses WHERE user_id = ? AND (category LIKE ? OR ? LIKE '%' || category || '%') ORDER BY id DESC LIMIT 1"
        search_text = f'%{text}%'
        result = await self._execute(query, (user_id, search_text, text))
        return result[0][0] if result else None

    async def get_db_status(self):
        result = await self._execute("SELECT COUNT(*) FROM expenses")
        return result[0][0] if result else 0

    async def get_expenses_count(self, user_id):
        query = "SELECT COUNT(*) FROM expenses WHERE user_id = ?"
        result = await self._execute(query, (user_id,))
        return result[0][0] if result else 0

    async def get_expenses_page(self, user_id, limit, offset):
        query = "SELECT id, amount, category, date FROM expenses WHERE user_id = ? ORDER BY date DESC ,id DESC LIMIT ? OFFSET ?"
        return await self._execute(query, (user_id, limit, offset))

    async def save_token(self, user_id, token):
        query = "INSERT INTO auth_tokens (user_id, token) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET token = ?"
        await self._execute(query, (user_id, token, token))

    async def get_token(self, user_id):
        result = await self._execute("SELECT token FROM auth_tokens WHERE user_id = ?", (user_id,))
        return result[0][0] if result else None

    async def delete_expense_by_id(self, record_id, user_id):
        query = "DELETE FROM expenses WHERE id = ? AND user_id = ?"
        await self._execute(query, (record_id, user_id))

    async def update_expense_amount(self, record_id, user_id, new_amount):
        query = "UPDATE expenses SET amount = ? WHERE id = ? AND user_id = ?"
        await self._execute(query, (new_amount, record_id, user_id))

    async def get_user_categories(self, user_id):
        base_categories = ["Їжа", "Транспорт", "Кава", "Покупки"]

        result = await self._execute("SELECT name FROM categories WHERE user_id = ?", (user_id,))

        if not result:
            return base_categories
        custom_categories = [row[0] for row in result]
        all_categories = base_categories.copy()
        for cat in custom_categories:
            if cat not in all_categories:
                all_categories.append(cat)
        return all_categories

    async def add_category(self, user_id, name):
        query = "INSERT OR IGNORE INTO categories (user_id, name) VALUES (?, ?)"
        await self._execute(query, (user_id, name))

    async def get_custom_categories(self, user_id):
        return await self._execute("SELECT id, name FROM categories WHERE user_id = ?", (user_id,))

    async def delete_category(self, cat_id, user_id):
        return await self._execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (cat_id, user_id,))

    async def rename_category(self, cat_id, user_id, new_name):
        old_name_data = await self._execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
        if old_name_data:
            old_name = old_name_data[0][0]

            await self._execute("UPDATE categories SET name = ? WHERE id = ? AND user_id = ?",
                                (new_name, cat_id, user_id))

            await self._execute("UPDATE expenses SET category = ? WHERE user_id = ? AND category = ?",
                                (new_name, user_id, old_name))
