import requests
import json
import time
from datetime import datetime, timezone, timedelta
from API import coingecko
from API import cryptocompare

SECONDS_IN_A_DAY = 86400
MINUTE_TO_SECONDS = 60

def isStableCoin(coin, stable_keywords):
    name = coin['name'].lower()
    symbol = coin['symbol'].lower()
    price = coin.get('current_price', 0)

    is_name_stable = any(kw in name or kw in symbol for kw in stable_keywords)
    is_price_stable = 0.99 <= price <= 1.01

    return is_name_stable or is_price_stable

def getTopCoins(num_of_top_coins, num_to_search, currency, config):
    # Only modify this part if another API needs to be used instead of CoinGecko
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': currency,
        'order': 'market_cap_desc',
        'per_page': num_to_search,
        'page': 1,
        'sparkline': 'false'
    }

    response = requests.get(url, params)
    response.raise_for_status()
    coins = response.json()

    stable_keywords = config.get("stable-coin-keywords", ['usd'])
    ignored_coins = config.get("coins_ignored", [])
    filtered_coins = [
        coin for coin in coins
        if not isStableCoin(coin, stable_keywords) and coin['symbol'].lower() not in ignored_coins
    ]
    top_coins = filtered_coins[:num_of_top_coins]

    coingecko.log(top_coins)

    return [(coin['symbol'].upper()) for coin in top_coins]

def wait_until_next_minute():
    now = datetime.now(timezone.utc)
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_seconds = (next_minute - now).total_seconds()
    time.sleep(wait_seconds)

def continuousCollection():
    last_top_symbols = set()
    last_run_day = None

    with open("config.json") as f:
        config = json.load(f)

    while True:
        wait_until_next_minute()

        try:
            with open("config.json") as f:
                config = json.load(f)

            num_of_top_coins = config.get("top-number-of-coins", 50)
            num_to_search = num_of_top_coins + config.get("selection-margin", 20)
            currency = config.get("currency", "usd")
            days = config.get("historical-data-days", 90)

            now = datetime.now(timezone.utc)
            current_day = now.date()
            seconds_today = now.hour * 3600 + now.minute * 60 + now.second

            if seconds_today >= SECONDS_IN_A_DAY - MINUTE_TO_SECONDS and last_run_day != current_day:
                print("[Daily Update] Fetching top coins and full history...")
                coins = getTopCoins(num_of_top_coins, num_to_search, currency, config)
                cryptocompare.collectHistoricalData(coins, currency, days)
                last_top_symbols = set(coins)
                last_run_day = current_day
            else: 
                coins = getTopCoins(num_of_top_coins, num_to_search, currency, config)
                new_symbols = [s for s in coins if s not in last_top_symbols]

                if new_symbols:
                    print("[Live Update] New coins detected:", new_symbols)
                    cryptocompare.collectHistoricalData(new_symbols, currency, days)
                    last_top_symbols.update(new_symbols)
                else:
                    print("[Live Update] No new coins, just logging.")

        except Exception as e:
            print(f"[error] {e}")

if __name__ == "__main__":
    continuousCollection()
