import requests
import json
from API import coingecko
from API import cryptocompare

def isStableCoin(coin, stable_keywords):
    name = coin['name'].lower()
    symbol = coin['symbol'].lower()
    price = coin.get('current_price', 0)

    is_name_stable = any(kw in name or kw in symbol for kw in stable_keywords)
    is_price_stable = 0.99 <= price <= 1.01

    return is_name_stable or is_price_stable

def getTopCoins(num_of_top_coins, num_to_search, currency):
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

if __name__ == "__main__":
    with open("config.json") as f:
        config = json.load(f)

    num_of_top_coins = config.get("top-number-of-coins", 50)
    num_to_search = num_of_top_coins + config.get("selection-margin", 20)
    currency = config.get("currency", "usd")
    days = config.get("historical-data-days", 90)

    coins = getTopCoins(num_of_top_coins, num_to_search, currency)
    cryptocompare.collectHistoricalData(coins, currency, days)

