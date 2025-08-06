# Cryptometrics Backend

A comprehensive cryptocurrency data collection system that fetches live market data, historical prices, news articles, and social media sentiment from multiple sources. The backend continuously monitors cryptocurrency markets and aggregates data for analysis and visualization.

## Overview

Cryptometrics connects to multiple APIs to collect:
- **Live Market Data**: Real-time price, market cap, and volume from CoinGecko
- **Historical Price Data**: Daily OHLCV data from CoinGecko and CryptoCompare
- **News Articles**: Cryptocurrency news with sentiment analysis from NewsAPI
- **Social Media**: Reddit posts with sentiment scoring from relevant subreddits
- **Sentiment Analysis**: Weighted sentiment scores combining news and social data

## Architecture

```
backend/
├── API/
│   ├── coingecko.py          # CoinGecko API integration
│   ├── cryptocompare.py      # CryptoCompare historical data
│   ├── news.py               # NewsAPI integration
│   ├── reddit.py             # Reddit API integration
│   ├── analysis/
│   │   ├── sentiment.py      # Sentiment analysis
│   │   ├── weightedSentiment.py  # Combined sentiment scoring
│   │   └── priceOutlier.py   # Price anomaly detection
│   └── maps/
│       └── subreddit_map.py  # Cryptocurrency subreddit mappings
├── logs/
│   ├── live_data/           # Real-time market data
│   ├── hist_data/           # Historical price data (CryptoCompare)
│   ├── hist_data_backup/    # Historical price data (CoinGecko)
│   ├── news_articles/       # News articles by cryptocurrency
│   └── reddit_posts/        # Reddit posts by cryptocurrency
├── collector.py             # Main data collection orchestrator
├── server.py               # Flask API server
├── config.json             # Configuration file
└── requirements.txt        # Python dependencies
```

## Installation

### Prerequisites
- Python 3.9+
- pip package manager

### Setup
1. Download the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys in `config.json` (see Configuration section)

4. Run the data collector:
```bash
python collector.py
```

5. (Optional) Start the API server:
```bash
python server.py
```

## Configuration (`config.json`)

The configuration file controls all aspects of data collection behavior. Each parameter affects how and when data is fetched from different sources.

### Market Data Collection

#### `market-update-frequency`
- **Type**: Integer (seconds)
- **Default**: 60
- **Effect**: Controls how often the main collection loop runs
- **Impact**: 
  - Lower values = more frequent market updates and API calls
  - Higher values = less frequent updates, reduced API usage
  - Minimum recommended: 60 seconds to avoid rate limits

#### `top-number-of-coins`
- **Type**: Integer
- **Default**: 50
- **Effect**: Number of top cryptocurrencies to track by market cap
- **Impact**:
  - More coins = more data collection across all sources
  - Increases API calls, storage, and processing time
  - Affects news and Reddit data collection volume

#### `selection-margin`
- **Type**: Integer
- **Default**: 20
- **Effect**: Additional coins to fetch beyond the top N to filter out stablecoins
- **Impact**:
  - Ensures you get exactly `top-number-of-coins` after filtering
  - Higher margin = more stable coin detection but more API calls
  - Recommended: 20-50% of `top-number-of-coins`

#### `currency`
- **Type**: String
- **Default**: "usd"
- **Effect**: Base currency for price data
- **Impact**:
  - Must match CoinGecko and CryptoCompare supported currencies
  - Affects all price calculations and historical data
  - Common options: "usd", "eur", "btc", "eth"

### Historical Data Configuration

#### `historical-data-days`
- **Type**: Integer
- **Default**: 90
- **Effect**: Number of days of historical price data to fetch
- **Impact**:
  - More days = larger initial data fetch and longer processing
  - Affects analysis capabilities and storage requirements
  - CoinGecko API limits may apply for longer periods

### Filtering and Selection

#### `stable-coin-keywords`
- **Type**: Array of strings
- **Default**: ["usd", "usdt", "usdc", "busd", "dai", "tusd", "usdp", "usdd", "gusd", "fdusd"]
- **Effect**: Keywords used to identify and filter out stablecoins
- **Impact**:
  - Prevents stablecoins from being included in top coins
  - Matching is case-insensitive against coin name and symbol
  - Add new stablecoin identifiers as they emerge

#### `coins_ignored`
- **Type**: Array of strings
- **Default**: ["cbbtc", "wsteth", "lbtc"]
- **Effect**: Specific coin symbols to exclude from collection
- **Impact**:
  - Manually removes unwanted coins (wrapped tokens, derivatives)
  - Symbols are matched case-insensitively
  - Useful for excluding synthetic or derivative tokens

### News Collection

#### `newsapi_key`
- **Type**: Array of strings
- **Effect**: NewsAPI keys for fetching cryptocurrency news
- **Impact**:
  - Multiple keys enable key rotation to avoid rate limits
  - Keys are used in round-robin fashion
  - More keys = higher news collection capacity
  - Each key allows ~1000 requests per day

#### `media-interval`
- **Type**: Integer (minutes)
- **Default**: 5
- **Effect**: How often to fetch news and Reddit data
- **Impact**:
  - Lower values = more frequent news updates but higher API usage
  - News sources update multiple times per hour
  - Minimum recommended: 5 minutes to avoid rate limits
  - Affects both news and Reddit collection timing

### Social Media Configuration

#### `KEYWORDS`
- **Type**: Array of strings
- **Default**: ["crypto statistics or news", "money gain or loss"]
- **Effect**: Keywords for zero-shot classification of relevant Reddit posts
- **Impact**:
  - Determines which Reddit posts are considered relevant
  - Uses BART model for semantic matching
  - More specific keywords = more precise filtering
  - Broader keywords = more posts but potentially less relevant

#### `BLOCKLIST`
- **Type**: Array of strings
- **Default**: ["joke", "funny", "shitpost", "troll", "satire", "sarcasm", "clown", "cringe", "banter", "comic", "gag"]
- **Effect**: Keywords to filter out non-serious content
- **Impact**:
  - Removes meme posts and joke content
  - Improves data quality for sentiment analysis
  - Case-insensitive matching against post title and content
  - Add terms specific to cryptocurrency meme culture

## Data Collection Behavior

### Collection Timing

1. **Every Minute**: 
   - Fetches top coins from CoinGecko
   - Logs live market data
   - Updates price outlier detection

2. **Every `media-interval` Minutes**:
   - Fetches news articles for all tracked coins
   - Collects Reddit posts from relevant subreddits
   - Computes weighted sentiment scores

3. **Daily (at 23:59 UTC)**:
   - Triggers full historical data update
   - Fetches complete price history for all coins
   - Updates both CoinGecko and CryptoCompare datasets

4. **New Coin Detection**:
   - When new coins enter the top N, immediately fetches their data
   - Collects full historical data and recent news/social media

### API Rate Limiting

The system implements several rate limiting strategies:

- **CoinGecko**: 3-second delays between historical requests
- **CryptoCompare**: 0.5-second delays between requests
- **NewsAPI**: Key rotation when rate limits hit
- **Reddit**: 0.5-second delays, 10-second delays between subreddits

### Data Storage

All data is stored in CSV format under the `logs/` directory:

- **Live Data**: Rolling 24-hour window
- **Historical Data**: Rolling 30-day window for performance
- **News Articles**: Rolling 7-day window
- **Reddit Posts**: Rolling 30-day window

## API Endpoints

The Flask server (`server.py`) provides REST endpoints for accessing collected data:

### `GET /api/files`
Returns the structure of all available CSV files grouped by folder.

### `GET /api/file/<folder>/<filename>`
Returns the contents of a specific CSV file as JSON.

### `GET /api/live`
Returns current live market data from `live_data/live_data.csv`.

### `GET /api/live_sentiment`
Returns current sentiment data from `live_data/live_sentiment.csv`.

## Configuration Examples

### High-Frequency Trading Setup
```json
{
  "market-update-frequency": 30,
  "top-number-of-coins": 20,
  "media-interval": 3,
  "historical-data-days": 30
}
```

### Research/Analysis Setup
```json
{
  "market-update-frequency": 300,
  "top-number-of-coins": 100,
  "media-interval": 15,
  "historical-data-days": 365
}
```

### Resource-Constrained Setup
```json
{
  "market-update-frequency": 300,
  "top-number-of-coins": 10,
  "media-interval": 30,
  "historical-data-days": 30
}
```

## Monitoring and Logs

The system provides console output for monitoring:
- `[CoinGecko]`: Live and historical market data updates
- `[CryptoCompare]`: Historical price data collection
- `[NewsAPI]`: News article fetching with API key rotation
- `[Reddit]`: Social media post collection
- `[Collector Error]`: Main loop errors and exceptions

## Dependencies

Core Python packages required:
- `requests`: HTTP API calls
- `transformers`: Sentiment analysis and zero-shot classification
- `flask`: API server
- `pandas`: Data manipulation (server only)
- `numpy`, `scipy`: Numerical computing
- `torch`: PyTorch for transformer models

## Troubleshooting

### Common Issues

1. **API Rate Limits**:
   - Increase delays in configuration
   - Add more NewsAPI keys
   - Reduce `top-number-of-coins`

2. **Memory Usage**:
   - Reduce `historical-data-days`
   - Decrease `top-number-of-coins`
   - Clear old log files periodically

3. **Missing Data**:
   - Check API key validity
   - Verify network connectivity
   - Review console logs for specific errors

### Performance Optimization

- Use SSD storage for faster CSV operations
- Consider database storage for larger datasets
- Implement data compression for long-term storage
- Monitor system resources during collection

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

For questions or issues, please open a GitHub issue.