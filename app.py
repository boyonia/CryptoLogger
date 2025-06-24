import json
import time
import os
from API.binance import BinanceStream
from API.coinbase import CoinbaseStream
# Add more Streams in the future here

def clearLogs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok = True)

    log_files = [
        os.path.join(log_dir, "coinbase_log.txt"),
        os.path.join(log_dir, "binance_log.txt")
        # Add more log files in the future here
    ]

    for file_path in log_files:
        with open(file_path, "w") as f:
            f.write("")

def main():
    clearLogs()
    
    with open("config.json") as f:
        config = json.load(f)

    binanceStream = None
    coinbaseStream = None
    # Add more Streams in the future here
    
    delay = config.get("delay", 5)

    for source in config["sources"]:
        name = source["name"].lower()
        for ws in source["sockets"]:
            if name == "binance":
                binanceStream = BinanceStream(ws["primary"], ws.get("backup"), delay)
                binanceStream.start()
            elif name == "coinbase":
                coinbaseStream = CoinbaseStream(ws["primary"], delay)
                coinbaseStream.start()
            # Add more Streams in the future here

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping streams...")
        if binanceStream:
            binanceStream.stop()
        if coinbaseStream:
            coinbaseStream.stop()
        # Add more Streams in the future here
        print("Exited")

if __name__ == "__main__":
    main()