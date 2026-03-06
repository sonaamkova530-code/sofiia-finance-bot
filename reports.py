import pandas as pd
import matplotlib.pyplot as plt



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


