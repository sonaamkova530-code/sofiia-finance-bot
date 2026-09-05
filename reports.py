import matplotlib.pyplot as plt
import pandas as pd


def create_balance_chart(income, spending, user_id):
    labels = ["Доходи", "Витрати"]
    values = [income, spending]
    colors = ['#4CAF50', '#FF5252']
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=colors)
    plt.title("Порівняння доходів та витрат", fontsize=14)
    plt.ylabel("Сума (грн)")

    for i, v in enumerate(values):
        plt.text(i, v + (max(values) * 0.02), str(v), ha='center', fontweight='bold')
    file_name = f"balance_chart_{user_id}.png"
    plt.savefig(file_name)
    plt.close()
    return file_name


def create_stats_chart(stats, user_id):
    if not stats:
        return None

    sorted_stats = sorted(stats, key=lambda x: x[1])
    categories = [row[0] for row in sorted_stats]
    amounts = [row[1] for row in sorted_stats]

    _fig, ax = plt.subplots(figsize=(8, len(categories) * 0.5 + 2))
    bars = ax.barh(categories, amounts, color='#4A4A4A', edgecolor='#E76F51', height=0.65)
    ax.set_title("Розподіл витрат за категоріями", fontsize=12, fontweight="bold", pad=15)
    ax.set_xlabel("Сума (грн)", fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add numeric labels at the end of each bar
    max_amount = max(amounts) if amounts else 1
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + (max_amount * 0.01),
            bar.get_y() + bar.get_height() / 2,
            f"{width:,.0f} ₴",
            va="center",
            fontsize=9
        )

    plt.tight_layout()
    file_name = f"stats_{user_id}.png"
    plt.savefig(file_name, dpi=200, bbox_inches="tight")
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


def create_weekly_chart(data, user_id):
    if not data:
        return None

    dates = [row[0][5:] for row in data]
    amounts = [row[1] for row in data]
    plt.figure(figsize=(10, 5))
    plt.plot(dates, amounts, marker='o', linestyle='-', color='#2ecc71', linewidth=2)
    plt.fill_between(dates, amounts, color='#2ecc71', alpha=0.2)
    for i, amount in enumerate(amounts):
        plt.text(dates[i], amount + (max(amounts) * 0.02),
                 f'{int(amount)}',
                 ha='center',
                 fontsize='10',
                 fontweight='bold',
                 color='#2c3e50')

    plt.title("Витрати за останній тиждень: ", fontsize=14)
    plt.ylabel("Грн")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    path = f"weekly_chart_{user_id}.png"
    plt.savefig(path)
    plt.close()
    return path
