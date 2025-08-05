import requests
import os
import csv
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from API import coingecko
from API import cryptocompare
from API import news
from API import reddit

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

    symbols = [coin['symbol'].upper() for coin in top_coins]
    names = [coin['name'] for coin in top_coins]
    ids = [coin['id'] for coin in top_coins]

    return symbols, names, ids

def waitUntilNextMinute():
    now = datetime.now(timezone.utc)
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_seconds = (next_minute - now).total_seconds()
    time.sleep(wait_seconds)

def continuousCollection():
    last_top_symbols = set()
    last_top_ids = set()
    last_top_names = set()
    last_run_day = None
    minute_counter = 0

    cc_thread = None
    cg_thread = None
    news_thread = None
    reddit_thread = None

    with open("config.json") as f:
        config = json.load(f)

    while True:
        waitUntilNextMinute()
        minute_counter += 1

        try:
            with open("config.json") as f:
                config = json.load(f)

            num_of_top_coins = config.get("top-number-of-coins", 50)
            num_to_search = num_of_top_coins + config.get("selection-margin", 20)
            currency = config.get("currency", "usd")
            days = config.get("historical-data-days", 90)
            media_interval = config.get("media-interval", 15)

            now = datetime.now(timezone.utc)
            current_day = now.date()
            seconds_today = now.hour * 3600 + now.minute * 60 + now.second

            coins, names, ids = getTopCoins(num_of_top_coins, num_to_search, currency, config)

            if minute_counter % media_interval == 0:
                if news_thread is None or not news_thread.is_alive():
                    news_thread = threading.Thread(target=news.fetchCryptoNews, args=(coins, names), daemon=True)
                    news_thread.start()
                if reddit_thread is None or not reddit_thread.is_alive():
                    reddit_thread = threading.Thread(target=reddit.fetchRedditPosts, args=(coins, config), daemon=True)
                    reddit_thread.start()
                minute_counter = 0

            if seconds_today >= SECONDS_IN_A_DAY - MINUTE_TO_SECONDS and last_run_day != current_day:
                print("[Daily Update] Fetching top coins and full history...")

                if cc_thread is None or not cc_thread.is_alive():
                    cc_thread = threading.Thread(target=cryptocompare.collectHistoricalData, args=(coins, currency, days), daemon=True)
                    cc_thread.start()

                if cg_thread is None or not cg_thread.is_alive():
                    cg_thread = threading.Thread(target=coingecko.collectHistoricalData, args=(coins, names, currency, days), daemon=True)
                    cg_thread.start()

                last_top_symbols = set(coins)
                last_top_ids = set(ids)
                last_top_names = set(names)
                last_run_day = current_day
            else: 
                new_symbols = [s for s in coins if s not in last_top_symbols]
                new_names = [n for n in names if n not in last_top_names]
                new_ids = [i for i in ids if i not in last_top_ids]

                if new_symbols:
                    print(f"[{datetime.now(timezone.utc)}] New coins detected:", new_symbols)
                    
                    if cc_thread is None or not cc_thread.is_alive():
                        cc_thread = threading.Thread(target=cryptocompare.collectHistoricalData, args=(new_symbols, currency, days), daemon=True)
                        cc_thread.start()

                    if cg_thread is None or not cg_thread.is_alive():
                        cg_thread = threading.Thread(target=coingecko.collectHistoricalData, args=(new_symbols, new_ids, currency, days), daemon=True)
                        cg_thread.start()

                    if news_thread is None or not news_thread.is_alive():
                        news_thread = threading.Thread(target=news.fetchCryptoNews, args=(new_symbols, new_names), daemon=True)
                        news_thread.start()

                    if reddit_thread is None or not reddit_thread.is_alive():
                        reddit_thread = threading.Thread(target=reddit.fetchRedditPosts, args=(new_symbols, config), daemon=True)
                        reddit_thread.start()

                    last_top_symbols.update(new_symbols)
                    last_top_ids.update(new_ids)
                    last_top_names.update(new_names)

        except Exception as e:
            print(f"[error] {e}")

if __name__ == "__main__":
    continuousCollection()
