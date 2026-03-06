import pandas as pd

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


