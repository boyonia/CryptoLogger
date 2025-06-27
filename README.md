# CryptoAPI Data Logger
```app.py```
This Python program connects simultaneously to Binance and Coinbase WebSocket APIs to stream live cryptocurrency trade data (price and volume) for BTC and ETH trading pairs. 

```collector.py```
This Python program gets data for the top 50 coins at the moment (excluding stable coins) from CoinGecko and gets historical data for all these coins for the past 3 months from CryptoCompare.

Both programs:
- Timestamped log entries normalized to UTC.
- Throttled logging frequency configurable via `config.json`.

---

## Project Structure

catcher/

├── API/
│ ├── binance.py
│ ├── coingecko.py
│ ├── cryptocompare.py
│ └── coinbase.py
├── logs/
│ ├── binance_log.txt
│ ├── coinbase_log.txt
│ ├── BTC.csv
│ ├── ETH.csv
│ ├── ...
│ ├── TRUMP.csv
│ └── coingecko_log.csv
├── app.py
├── collector.py
├── config.json
├── requirements.txt
└── README.md

---
## Requirements
- Python 3.11+
- Packages:
	-  `websocket-client`
	- `requests`

Install dependencies via:
```
pip install -r requirements.txt
```

## Usage
Run the main program:
```bash
python  app.py
```
or
```bash
python collector.py
```
This will:
- Read `config.json`
- Start WebSocket streams/connections for APIs
- Log historical or live data to respective log files

Use `Ctrl+C` to gracefully stop the program

---
## Logging Format
Logs are appended to files in the `logs/` folder with entries like:

``
{symbol}.csv
`` (example ``BTC.csv``)
| Date       | Open     | High     | Low      | Close    | Volume         |
|------------|----------|----------|----------|----------|----------------|
| 2025-03-30 | 82625.65 | 83516.72 | 81563.47 | 82379.51 | 839590269.08   |
| 2025-03-31 | 82379.51 | 83917.40 | 81290.13 | 82539.52 | 1894666416.64  |
| 2025-04-01 | 82539.52 | 85554.98 | 82419.98 | 85174.96 | 1962356062.59  |
| 2025-04-02 | 85174.96 | 88505.24 | 82299.20 | 82490.58 | 3519914220.40  |
| 2025-04-03 | 82490.58 | 83928.41 | 81178.57 | 83158.80 | 2335462308.44  |
| 2025-04-04 | 83158.80 | 84716.02 | 81648.68 | 83860.21 | 3085885741.07  |
| 2025-04-05 | 83860.21 | 84230.44 | 82357.52 | 83503.37 | 622496989.40   |
| 2025-04-06 | 83503.37 | 83756.10 | 77079.93 | 78365.57 | 2374631982.20  |
| 2025-04-07 | 78365.57 | 81172.27 | 74426.93 | 79143.06 | 5546499783.12  |
| 2025-04-08 | 79143.06 | 80835.83 | 76181.24 | 76255.10 | 3084760820.88  |

``
{api}.csv
`` (example ``coingecko.csv``)
| Timestamp     | Symbol | Price     | Market Cap     | Total Volume   | 24h Price Change (%) | 24h Market Cap Change (%) |
|---------------|--------|-----------|----------------|----------------|------------------------|----------------------------|
| 12:35:02.229  | btc    | 107190    | 2131455651436  | 31514043904    | 0.12328                | 0.09653                    |
| 12:35:02.229  | eth    | 2443.93   | 294888666880   | 18149262316    | 0.99369                | 0.82592                    |
| 12:35:02.229  | xrp    | 2.17      | 127796191896   | 2225314671     | -1.09381               | -1.02644                   |
| 12:35:02.229  | bnb    | 643.22    | 93829511886    | 659794268      | -0.58924               | -0.6376                    |
| 12:35:02.229  | sol    | 143.38    | 76609520799    | 3802918286     | -1.60658               | -1.06942                   |
| 12:35:02.229  | trx    | 0.271099  | 25702310046    | 566669467      | -0.53095               | -0.58762                   |
| 12:35:02.229  | doge   | 0.161117  | 24142559096    | 965597468      | -2.19322               | -2.32091                   |
| 12:35:02.229  | steth  | 2442.17   | 22348684630    | 18632883       | 0.97882                | 0.86321                    |
| 12:35:02.229  | ada    | 0.560103  | 20236235400    | 553364995      | -2.9181                | -2.88729                   |
| 12:35:02.229  | wbtc   | 107170    | 13799053714    | 237872356      | 0.25949                | 0.12163                    |

``
{api}.txt
`` (example ``binance.text``)
| UTC Time       | Symbol   | Price         | Volume        |
|----------------|----------|---------------|---------------|
| 05:21:14.428   | BTCUSDT  | $107422.70    | 0.00004000    |
| 05:21:15.131   | BTCUSDT  | $107422.69    | 0.01820000    |
| 05:21:15.953   | BTCUSDT  | $107422.69    | 0.00040000    |
| 05:21:17.283   | ETHUSDT  | $2439.22      | 0.05000000    |
| 05:21:18.104   | BTCUSDT  | $107422.69    | 0.02011000    |
| 05:21:18.827   | ETHUSDT  | $2439.55      | 0.10900000    |

## Extending
- Extend to store data in databases (e.g., SQLite, Postgres).