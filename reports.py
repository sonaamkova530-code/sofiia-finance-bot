def format_expense_report(data, period_name):
    if not data:
        return f"За {period_name} витрат немає."
    else:
        total = sum(r[0] for r in data)
        report = f"*Витрати за: {period_name}*\n"
        report += "\n".join(f"- {r[0]} грн | ({r[1]})" for r in data)
        report += f"\n\n*Всього {total} грн*"
        return report


