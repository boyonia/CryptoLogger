
# CryptoAPI Data Logger
This Python program connects simultaneously to Binance and Coinbase WebSocket APIs to stream live cryptocurrency trade data (price and volume) for BTC and ETH trading pairs. It logs the data with timestamps into separate log files for each exchange and prints progress to the terminal.

---

## Features

- Connects to Binance and Coinbase WebSocket APIs concurrently using multithreading.
- Currently subscribes to BTC and ETH trading pairs.
- Logs latest price and volume data to:
  - `logs/binance_log.txt`
  - `logs/coinbase_log.txt`
- Timestamped log entries normalized to UTC with millisecond precision.
- Throttled logging frequency configurable via `config.json`.
- Supports primary and backup WebSocket endpoints for Binance.
- Gracefully handles WebSocket disconnects and unsubscriptions.

---

## Project Structure
	catcher/  
	├── API/  
	│ ├── binance.py  
	│ └── coinbase.py  
	├── logs/  
	│ ├── binance_log.txt  
	│ └── coinbase_log.txt  
	├── app.py  
	├── config.json  
	├── requirements.txt  
	└── README.md
---

## Requirements

- Python 3.9+
- Packages:
  - `websocket-client`

Install dependencies via:
```
pip install -r requirements.txt
```

## Usage

Run the main program:

```bash
python app.py
```
This will:

- Read `config.json`
- Start WebSocket streams for Binance and Coinbase concurrently
- Log BTC and ETH price/volume updates to respective files
- Print data logging activity timestamps to console
- Use `Ctrl+C` to gracefully stop the program

---

## Logging Format

Logs are appended to files in the `logs/` folder with entries like:
```bash
UTC: 14:25:30.123    BTCUSDT: $30000.12    Volume: 0.45T    ETHUSDT: $2000.34    Volume: 1.23T
UTC: 14:25:32.124    BTC-USD: $29950.11    Volume: 0.67T
```
-   `UTC` timestamps are in HH:MM:SS.milliseconds format.
-   Volume suffix `T` is added for readability (e.g., trade size).

## Extending
- Add more symbols by modifying the subscription lists in `binance.py` and `coinbase.py`.
- Extend to store data in databases (e.g., SQLite, Postgres).
- Enhance error handling and automatic reconnection logic.