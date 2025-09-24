import os
import csv
import pandas as pd
from datetime import datetime

def getAverageNewsSentiments(symbol):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'news_articles', f'{symbol.upper()}.csv'))

    if not os.path.exists(path):
        return 0.0, 0

    df = pd.read_csv(path)
    if 'sentiment_score' not in df.columns:
        return 0.0, 0

    scores = df['sentiment_score'].dropna().astype(float)
    count = len(scores)

    if count < 3:
        return 0.0, count

    avg_score = scores.mean()
    return avg_score, count

def getAverageRedditSentiments(symbol):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'reddit_posts', f'{symbol.upper()}.csv'))
    
    if not os.path.exists(path):
        return 0.0, 0

    df = pd.read_csv(path)
    if 'sentiment_score' not in df.columns:
        return 0.0, 0

    scores = df['sentiment_score'].dropna().astype(float)
    count = len(scores)

    if count < 3:
        return 0.0, count

    avg_score = scores.mean()
    return avg_score, count

def log(results):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'live_data', 'live_sentiment.csv'))
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'weighted_score', 'news_score', 'reddit_score', 'news_count', 'reddit_count'])
        writer.writeheader()

        for result in results:
            writer.writerow(result)

def computeWeightedSentiment(symbols):
    results = []

    for symbol in symbols:
        news_score, news_count = getAverageNewsSentiments(symbol)
        reddit_score, reddit_count = getAverageRedditSentiments(symbol)
        if reddit_count == 0:
            weighted_score = news_score
        elif news_count == 0:
            weighted_score = 0.0
        else: 
            weighted_score = 0.8 * news_score + 0.2 * reddit_score

        results.append({
            'symbol': symbol.upper(),
            'weighted_score': round(weighted_score, 4),
            'news_score': round(news_score, 4),
            'reddit_score': round(reddit_score, 4),
            'news_count': news_count,
            'reddit_count': reddit_count
        })

    log(results)

    print(f"[Analysis] Weighted sentiment score calculated")

