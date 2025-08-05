import csv
import os
import requests
import time
import json
from .analysis import sentiment
from datetime import datetime, timezone, timedelta

current_api_key_index = 0

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[NewsAPI] Error loading config: {e}")
        return None

def log(symbol, articles):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs/news_articles")
    os.makedirs(log_dir, exist_ok = True)
    log_path = os.path.join(log_dir, f"{symbol}.csv")

    existing_entries = []
    seen_urls = set()
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    if os.path.exists(log_path):
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    published_at = datetime.fromisoformat(row['published_at'].replace('Z', '+00:00')) \
                        if 'Z' in row['published_at'] else datetime.fromisoformat(row['published_at'])

                    if published_at >= one_week_ago:
                        row['published_at'] = published_at
                        existing_entries.append(row)
                        seen_urls.add(row['url'])  # Use URL as a unique identifier
                except Exception as e:
                    continue  # skip malformed rows

    for article in articles:
        url = article.get('url', '')
        if url in seen_urls:
            continue  # skip duplicates

        title = article.get('title', '')
        source_name = article.get('source', {}).get('name', '')
        content = article.get('content', '')
        sentiment_score = sentiment.getSentimentScore(f"{title} {source_name} {content}")
        published_at_str = article.get('publishedAt', '')

        try:
            published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
        except Exception:
            published_at = datetime.now(timezone.utc)

        if published_at < one_week_ago:
            continue  # Skip if too old

        existing_entries.append({
            'title': title,
            'source_name': source_name,
            'url': url,
            'published_at': published_at,
            'sentiment_score': sentiment_score,
        })

    # Sort newest first by parsed publish time
    existing_entries.sort(key=lambda x: x['published_at'], reverse=True)

    # Write to CSV (excluding _parsed_published_at)
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['title', 'source_name', 'url', 'published_at', 'sentiment_score']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_entries)

    print(f"[NewsAPI] News data logged for: {symbol}")

def isRelevantArticle(article, target_coin_name, target_symbol, other_crypto_symbols):
    # Filter articles to ensure they're primarily about the target cryptocurrency
    title = article.get('title', '').lower()
    description = article.get('description', '').lower() if article.get('description') else ''
    content = article.get('content', '').lower() if article.get('content') else ''
    
    # Combine all text for analysis
    full_text = f"{title} {description} {content}"
    
    # Dynamic target keywords based on coin name and symbol
    target_keywords = [target_coin_name.lower(), target_symbol.lower()]
    
    # Remove duplicates and empty strings
    target_keywords = list(set([kw for kw in target_keywords if kw]))
    
    # Use other crypto symbols passed in (excluding current target)
    other_crypto_keywords = [symbol.lower() for symbol in other_crypto_symbols 
                           if symbol.lower() not in target_keywords]
    
    # Must have target keyword in title (most restrictive check)
    title_has_target = any(keyword in title for keyword in target_keywords)
    if not title_has_target:
        return False
    
    # Check target mentions vs other crypto mentions
    target_mentions_title = sum(title.count(keyword) for keyword in target_keywords)
    target_mentions_full = sum(full_text.count(keyword) for keyword in target_keywords)
    
    other_mentions_title = sum(title.count(keyword) for keyword in other_crypto_keywords)
    other_mentions_full = sum(full_text.count(keyword) for keyword in other_crypto_keywords)
    
    # Reject if other cryptos are mentioned more prominently in title
    if other_mentions_title > target_mentions_title:
        return False
    
    # For articles mentioning multiple cryptos, require target to be mentioned at least twice as much
    if other_mentions_full > 0 and target_mentions_full < (other_mentions_full * 2):
        return False
    
    # Additional check: reject articles that are clearly about general crypto market rather than specific coin
    general_crypto_terms = ['cryptocurrency', 'crypto market', 'digital assets', 'blockchain market', 'altcoin']
    general_mentions = sum(full_text.count(term) for term in general_crypto_terms)
    
    # If general terms dominate and target mentions are low, likely not specific enough
    if general_mentions > target_mentions_full and target_mentions_full < 3:
        return False
    
    return True

def get_next_api_key():
    """Get the next API key in rotation"""
    global current_api_key_index
    config = load_config()
    if not config or 'newsapi_key' not in config:
        return None
    
    api_keys = config['newsapi_key']
    if current_api_key_index >= len(api_keys):
        current_api_key_index = 0
    
    api_key = api_keys[current_api_key_index]
    current_api_key_index += 1
    return api_key

def fetchCoinNews(coin_name, coin_symbol, other_crypto_symbols):
    url = "https://newsapi.org/v2/everything"

    now = datetime.now(timezone.utc)
    from_date = (now - timedelta(days=15)).strftime('%Y-%m-%dT%H:%M:%SZ')  # 15 days
    to_date = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Dynamic search query using coin name and symbol
    search_query = f'"{coin_name}" OR "{coin_symbol}"'
    
    config = load_config()
    
    api_keys = config['newsapi_key']
    max_retries = len(api_keys)
    
    for attempt in range(max_retries):
        api_key = get_next_api_key()
        if not api_key:
            print("[NewsAPI] No API keys available")
            return []
        
        params = {
            'q': search_query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'from': from_date,
            'to': to_date,
            'pageSize': 100,
            'apiKey': api_key
        }

        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 429:
                print(f"[NewsAPI] API key {current_api_key_index}/{len(api_keys)} hit rate limit, trying next key...")
                continue
            
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            
            # Filter articles to ensure relevancy
            filtered_articles = [
                article for article in articles 
                if isRelevantArticle(article, coin_name, coin_symbol, other_crypto_symbols)
            ]
            
            print(f"[NewsAPI] Filtered {len(articles)} articles down to {len(filtered_articles)} relevant articles for {coin_name} using API key {current_api_key_index}")
            return filtered_articles
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print(f"[NewsAPI] API key {current_api_key_index}/{len(api_keys)} hit rate limit, trying next key...")
                continue
            else:
                print(f"[NewsAPI] HTTP error with API key {current_api_key_index}: {e}")
                continue
        except Exception as e:
            print(f"[NewsAPI] Error with API key {current_api_key_index}: {e}")
            continue
    
    print("[NewsAPI] All API keys exhausted or failed")
    return []

def fetchCryptoNews(coins, names):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_dir = os.path.join(base_dir, "logs/news_articles")
    os.makedirs(hist_dir, exist_ok=True)

    # Create list of all symbols for filtering
    all_symbols = coins + names
    
    for coin, name in zip(coins, names):
        file_path = os.path.join(hist_dir, f"{coin.upper()}.csv")
        if os.path.exists(file_path):
            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)
            if datetime.now(timezone.utc) - last_modified < timedelta(minutes=15):
                print(f"[NewsAPI] Skipping {name} ({coin}), news already up to date.")
                continue

        # Get other crypto symbols for filtering (exclude current coin)
        other_symbols = [s for s in all_symbols if s.lower() not in [coin.lower(), name.lower()]]
        
        data = fetchCoinNews(name, coin, other_symbols)
        log(coin, data)
        print(f"[NewsAPI] {name} ({coin}) news logged")
        time.sleep(2)  # Add 2 second delay between requests