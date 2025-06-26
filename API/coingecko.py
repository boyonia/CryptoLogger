import csv
import os
from datetime import datetime, timezone

def log(coins):
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok = True)
    log_path = os.path.join(log_dir, "coingecko_log.csv")

    file_exists = os.path.isfile(log_path)
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                'timestamp',
                'symbol',
                'price',
                'market_cap',
                'total_volume',
                'price_change_pct_24h',
                'market_cap_change_pct_24h'
            ])

        for coin in coins:
            writer.writerow([
                timestamp,
                coin['symbol'],
                coin['current_price'],
                coin['market_cap'],
                coin['total_volume'],
                coin.get('price_change_percentage_24h', 0.0),
                coin.get('market_cap_change_percentage_24h', 0.0)
            ])
    