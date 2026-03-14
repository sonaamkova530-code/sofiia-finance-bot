import requests


def get_exchange_rate(currency_code="EUR"):
    url = "https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5"

    try:
        response = requests.get(url, timeout=10)  # Додаємо таймаут 10 секунд
        if response.status_code != 200:
            print(f"ПриватБанк відповів помилкою: {response.status_code}")
            return None

        data = response.json()

        for item in data:
            if item['ccy'] == currency_code.upper():
                return round(float(item['buy']), 2)

        return None
    except Exception as e:
        print(f"Помилка ПриватБанку: {e}")
        return None