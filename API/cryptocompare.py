import csv
import os
import requests
import time
from datetime import datetime

SYMBOL_OVERRIDES = {
    'MNT': 'MANTLE'
}

def log(symbol, history):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok = True)
    log_path = os.path.join(log_dir, f"{symbol}.csv")

    existing_data = {}

    # Step 1: Read existing data
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row['date']] = row

    # Step 2: Filter to last 30 days
    cutoff = datetime.now().date().toordinal() - 30
    existing_data = {
        date: row for date, row in existing_data.items()
        if datetime.strptime(date, '%Y-%m-%d').date().toordinal() >= cutoff
    }

    # Step 3: Merge new data
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

    # Step 4: Write updated data back to CSV
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['date', 'open', 'high', 'low', 'close', 'volume']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Sort by date ascending
        for date in sorted(existing_data.keys()):
            writer.writerow(existing_data[date])

def fetchDailyHistory(symbol, currency, days):
    symbol = SYMBOL_OVERRIDES.get(symbol.upper(), symbol.upper())

    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {
        'fsym': symbol,
        'tsym': currency,
        'limit': days - 1
    }

    response = requests.get(url, params)
    response.raise_for_status()
    data = response.json()

    return data['Data']['Data']

def collectHistoricalData(symbols, currency, days):
    for symbol in symbols:
        try:
            print(f"Fetching: {symbol}")
            history = fetchDailyHistory(symbol, currency, days)
            log(symbol, history)
            time.sleep(0.5)  # Avoid rate limit
        except Exception as e:
            print(f"Failed for {symbol}: {e}")
