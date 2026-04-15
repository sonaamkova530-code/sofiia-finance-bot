# 📊 Personal Finance Tracker & Analytics Dashboard

A full-stack hybrid application designed to help users track their personal expenses effortlessly via a Telegram Bot,
while providing a comprehensive, secure web dashboard for data visualization and analytics.

## 🚀 Key Features

* **Smart Telegram Integration:** Quick and intuitive logging of daily expenses, categorized with just a few taps.
* **Secure Web Dashboard:** A responsive web interface displaying interactive charts, real-time budget status, and
  detailed transaction history.
* **Token-Based Security:** Dynamic, URL-safe access tokens (`?token=...`) ensure that users can only view their own
  financial reports without needing a heavy authentication system.
* **Visual Analytics:** Interactive pie charts for expense breakdown by category and budget overflow alerts.
* **Unified Database:** Both the bot and the web dashboard share a synchronized SQLite database, ensuring data is always
  up-to-date.

## 🛠️ Tech Stack

* **Backend:** Python 3.x, FastAPI
* **Bot Framework:** pyTelegramBotAPI (Async)
* **Database:** SQLite3
* **Frontend:** HTML5, CSS3, JavaScript (Chart.js for rendering graphics)

## 🧠 Technical Highlights

This project demonstrates practical knowledge in several key backend concepts:

1. **Application Architecture:** Clear separation of database queries, business logic, and UI rendering.
2. **Security Implementation:** Generating and validating secure cryptographic tokens for protected route access.
3. **Data Aggregation:** Complex SQL queries to calculate total expenses, count operations, and group data for chart
   rendering.
4. **Hybrid System Design:** Bridging a messaging bot ecosystem with a synchronous/asynchronous web framework.

## ⚙️ How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/sonaamkova530-code/sofiia-finance-bot.git