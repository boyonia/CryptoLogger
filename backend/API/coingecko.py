import csv
import os
import requests
import time
from .analysis import priceOutlier
from datetime import datetime, timezone, timedelta

def log(coins):
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    cutoff = now - timedelta(hours=24)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs", "live_data")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "live_data.csv")

    # Load existing entries and filter out ones older than 24 hours
    filtered_entries = []
    if os.path.exists(log_path):
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row_time = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
                    if row_time >= cutoff:
                        filtered_entries.append(row)
                except Exception:
                    continue  # Skip rows with invalid or missing timestamps

    # Append new entries
    for coin in coins:
        # Replace this with actual outlier detection logic
        price_outlier_flag = 't' if priceOutlier.isPriceOutlier(coin['symbol'].upper(), coin['current_price']) else 'f'

        entry = {
            'timestamp': timestamp,
            'symbol': coin['symbol'].upper(),
            'price': coin['current_price'],
            'market_cap': coin['market_cap'],
            'total_volume': coin['total_volume'],
            'price_change_pct_24h': coin.get('price_change_percentage_24h', 0.0),
            'market_cap_change_pct_24h': coin.get('market_cap_change_percentage_24h', 0.0),
            'price_outlier_flag': price_outlier_flag
        }
        filtered_entries.append(entry)

    # Rewrite the CSV file with the updated list
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'timestamp',
            'symbol',
            'price',
            'market_cap',
            'total_volume',
            'price_change_pct_24h',
            'market_cap_change_pct_24h',
            'price_outlier_flag'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_entries)

    print(f"[CoinGecko] Live data logged.")

def logHistorical(symbol, history):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs/hist_data_backup")
    os.makedirs(log_dir, exist_ok = True)
    log_path = os.path.join(log_dir, f"{symbol}.csv")

    existing_data = {}

    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row['date']] = row

    cutoff = datetime.now().date().toordinal() - 30
    existing_data = {
        date: row for date, row in existing_data.items()
        if datetime.strptime(date, '%Y-%m-%d').date().toordinal() >= cutoff
    }

    for entry in history:
        date = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d')
        if date not in existing_data:
            existing_data[date] = {
                'date': date,
                'open': entry['open'],
                'high': entry['high'],
                'low': entry['low'],
                'close': entry['close'],
                'volume': entry['volumeto'],
            }
    
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['date', 'open', 'high', 'low', 'close', 'volume']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Sort by date ascending
        for date in sorted(existing_data.keys()):
            writer.writerow(existing_data[date])

    print(f"[CoinGecko] Historical data fetched for: {symbol}")

def fetchDailyHistory(name, currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{name}/market_chart"
    params = {
        'vs_currency': currency.lower(),
        'days': days,
        'interval': 'daily'
    }

    headers = {
        'x-cg-demo-api-key': "CG-sj1ZEEQGq8xie1ow9BeHrvbg"
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()

    prices = data['prices']
    volumes = {
        datetime.fromtimestamp(int(ts / 1000), tz=timezone.utc).strftime('%Y-%m-%d'): vol
        for ts, vol in data['total_volumes']
    }
    history = []

    for i, (ts, price) in enumerate(prices): 
        date_str = datetime.fromtimestamp(int(ts / 1000), tz=timezone.utc).strftime('%Y-%m-%d')

        entry = {
            'time': int(ts/1000),
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volumeto': volumes.get(date_str, 0)
        }

        if i + 1 < len(prices):
            current_price = price
            next_price = prices[i + 1][1]
            entry['close'] = next_price
            entry['high'] = max(current_price, next_price)
            entry['low'] = min(current_price, next_price)

        history.append(entry)

    return history

def collectHistoricalData(symbols, names, currency, days):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_dir = os.path.join(base_dir, "logs/hist_data_backup")
    os.makedirs(hist_dir, exist_ok=True)

    for symbol, coin_id in zip(symbols, names):
        file_path = os.path.join(hist_dir, f"{symbol.upper()}.csv")
        if os.path.exists(file_path):
            with open(file_path, 'r', newline='') as f:
                reader = list(csv.DictReader(f))
                if reader:
                    last_date = reader[-1]['date']
                    last_date_obj = datetime.strptime(last_date, "%Y-%m-%d").date()
                    if (datetime.now(timezone.utc).date() - last_date_obj).days < 1:
                        print(f"[CoinGecko] Skipping {symbol}, data already up to date.")
                        continue

        try:
            print(f"[CoinGecko] Fetching: {coin_id}")
            history = fetchDailyHistory(coin_id, currency, days)
            logHistorical(symbol, history)
            time.sleep(3)
        except Exception as e:
            print(f"Failed for {coin_id}: {e}")