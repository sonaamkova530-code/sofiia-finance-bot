import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def create_balance_chart(income, spending, user_id):
    labels = ["Доходи", "Витрати"]
    values = [income, spending]
    colors = ['#4CAF50', '#FF5252']
    plt.figure(figsize = (8, 5))
    plt.bar(labels, values, color= colors)
    plt.title("Порівняння доходів та витрат", fontsize = 14)
    plt.ylabel("Сума (грн)")

    for i, v in enumerate(values):
        plt.text(i, v + (max(values) * 0.02), str(v), ha='center', fontweight = 'bold')
    file_name = f"balance_chart_{user_id}.png"
    plt.savefig(file_name)
    plt.close()
    return file_name



def create_stats_chart(stats, user_id):
    if not stats:
        return None

    categories = [row[0] for row in stats]
    amounts = [row[1] for row in stats]

    plt.figure(figsize = (6, 6))
    plt.pie(amounts, labels = categories, autopct = "%1.1f%%", startangle=140)
    plt.title("Розподіл витрат за категоріями:")
    file_name = f"stats_{user_id}.png"
    plt.savefig(file_name)
    plt.close()
    return file_name

def create_excel_report(data, user_id):
    if not data:
        return None

    df = pd.DataFrame(data, columns=["Дата", "Категорія", "Сума (грн)"])

    file_name = f"report_{user_id}.xlsx"

    df.to_excel(file_name, index=False)
    return file_name


def format_expense_report(data, period_name):
    if not data:
        return f"За {period_name} витрат немає."
    else:
        total = sum(r[0] for r in data)
        report = f"*Витрати за: {period_name}*\n"
        report += "\n".join(f"- {r[0]} грн | ({r[1]})" for r in data)
        report += f"\n\n*Всього {total} грн*"
        return report


