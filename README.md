# 📊 Personal Finance Tracker & Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=flat&logo=sqlite&logoColor=white)

A full-stack hybrid asynchronous application designed to help users track their personal expenses effortlessly via a
Telegram Bot, while providing a comprehensive, secure, and highly optimized web dashboard for data visualization.

## 🚀 Key Features

* **Smart Telegram Integration:** Quick and intuitive logging of daily expenses, categorized with just a few taps.
* **High-Performance Web Dashboard:** A responsive web interface displaying interactive charts (Chart.js), real-time
  budget status, and detailed transaction history.
* **Advanced Caching:** Integrated Redis caching to minimize database load and ensure lightning-fast dashboard
  rendering (304 Not Modified optimization).
* **Token-Based Security:** Dynamic, URL-safe access tokens (`?token=...`) ensure that users can only view their own
  financial reports without the overhead of a heavy authentication system.
* **Unified Hybrid Architecture:** Both the asynchronous bot and the FastAPI web dashboard run concurrently in a single
  event loop, sharing a synchronized SQLite database.

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, Uvicorn
* **Bot Framework:** pyTelegramBotAPI (Async)
* **Caching & Orchestration:** Redis, Docker, fastapi-cache2
* **Database:** SQLite3
* **Frontend / Templates:** Jinja2, HTML5, CSS3, JavaScript (Chart.js)

## 🧠 Technical Highlights

This project demonstrates strong practical knowledge in modern backend engineering:

* **Clean Architecture:** Strict separation of concerns — `run.py` acts purely as the application entry point, while
  `api.py` handles configuration, lifespan events, and routing.
* **Asynchronous I/O:** Extensive use of `asyncio.gather` for concurrent execution of the bot polling and API server.
* **Modern API Lifespan:** Proper resource management using FastAPI's `@asynccontextmanager` for safe Redis connection
  handling on startup and shutdown.
* **Data Aggregation:** Optimized SQL queries to calculate total expenses, count operations, and group data dynamically
  for UI rendering.

## ⚙️ How to Run Locally

**1. Clone the repository:**

```bash
git clone [https://github.com/sonaamkova530-code/sofiia-finance-bot.git](https://github.com/sonaamkova530-code/sofiia-finance-bot.git)
cd sofiia-finance-bot
```

**2. Set up the virtual environment and dependencies:**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**3. Start the Redis container (Docker required):**

```bash
docker run --name my-redis -p 6379:6379 -d redis
```

**4. Configure Environment Variables (if needed):**
Create a `.env` file in the root directory and add your Telegram Bot Token.

**5. Run the application (Bot & API concurrently):**

```bash
python run.py
```