import csv
import os
import requests
import time
from collections import defaultdict
from transformers import pipeline
from .analysis import sentiment
from .maps.subreddit_map import known_subs
from datetime import datetime, timezone, timedelta

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def log(symbol, posts):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs", "reddit_posts")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{symbol}.csv")

    existing_entries = []
    seen_ids = set()
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # Read existing posts and filter for last 30 days
    if os.path.exists(log_path):
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    created = datetime.fromisoformat(row['created_utc'])
                    if created >= one_month_ago:
                        existing_entries.append(row)
                        seen_ids.add(row['post_id'])  # track IDs to avoid duplicates
                except Exception:
                    continue  # skip malformed rows

    # Append only new posts (no duplicates)
    for post in posts:
        post_id = post.get('id', '')
        if post_id in seen_ids:
            continue  # skip duplicates

        title = post.get('title', '')
        selftext = post.get('selftext', '')
        sentiment_score = sentiment.getSentimentScore(f"{title} {selftext}")
        created_utc = post.get('created_utc', 0)

        new_entry = {
            'post_id': post_id,
            'subreddit': post.get('subreddit', ''),
            'title': title,
            'score': post.get('score', 0),
            'created_utc': datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat(sep=' '),
            'sentiment_score': sentiment_score,
        }

        existing_entries.append(new_entry)
        seen_ids.add(post_id)  # add new ID

    # Sort entries newest first
    existing_entries.sort(key=lambda x: datetime.fromisoformat(x['created_utc']), reverse=True)

    # Write all entries back to CSV
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['post_id', 'subreddit', 'title', 'score', 'created_utc', 'sentiment_score']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_entries)
    
    print(f"[Reddit] Reddit posts logged for: {symbol}")

def get_account_creation_utc(username):
    headers = {'User-Agent': 'CryptoTextCollector/1.0'}
    url = f'https://www.reddit.com/user/{username}/about.json'
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            print(f"[Reddit] Rate limit hit. Skipping {username}.")
            return None
        if response.status_code == 200:
            return response.json().get('data', {}).get('created_utc')
        else:
            print(f"[Reddit] Failed to fetch user info for u/{username} - Status {response.status_code}")
    except Exception as e:
        print(f"[Reddit] Error fetching user info: {e}")
    return None

def isRelevant(text, blocklist):
    text = text.lower()
    if any(bad in text for bad in blocklist):
        return False
    return True

def isZeroShotRelevant(text, keywords, threshold=0.4):
    result = classifier(text, candidate_labels=keywords, multi_label=False)
    top_label = result["labels"][0]
    top_score = result["scores"][0]
    return top_label in keywords and top_score >= threshold

def isProbablyBot(post, posts_by_author, karma_threshold=5, ratio_threshold=0.3, account_age_days=7, max_daily_posts=10):
    score = post.get('score', 0)
    upvote_ratio = post.get('upvote_ratio', 1.0)
    account_created_utc = post.get('author_created_utc')
    author = post.get('author')

    now_ts = datetime.now(timezone.utc).timestamp()
    is_low_karma = score < karma_threshold
    is_low_ratio = upvote_ratio < ratio_threshold
    is_new_account = account_created_utc and (now_ts - account_created_utc < account_age_days * 86400)

    recent_post_count = sum(
        1 for p in posts_by_author.get(author, [])
        if (now_ts - p.get('created_utc', 0)) <= 86400
    )

    posts_too_frequent = recent_post_count > max_daily_posts

    return (is_low_karma and is_low_ratio and is_new_account) or posts_too_frequent

def fetchSubreddit(subreddit, config):
    url = f"https://www.reddit.com/r/{subreddit}/top.json"
    headers = {'User-Agent': 'CryptoTextCollector/1.0'}
    params = {'limit': 50, 't': 'week'}

    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 429:
            print(f"[Reddit] Rate limit hit. Skipping {subreddit}.")
            return None

        response.raise_for_status()
        data = response.json()

        posts = []
        now_utc = datetime.now(timezone.utc).timestamp()
        three_days_ago = now_utc - 3 * 86400

        for item in data.get('data', {}).get('children', []):
            post = item.get('data', {})
            if post.get('created_utc', 0) < three_days_ago:
                continue

            author = post.get('author')
            if author and author != '[deleted]':
                time.sleep(0.5)
                post['author_created_utc'] = get_account_creation_utc(author)
            else:
                post['author_created_utc'] = None

            posts.append(post)

        posts_by_author = defaultdict(list)
        for post in posts:
            posts_by_author[post['author']].append(post)

        filtered = []
        for post in posts:
            post_id = post.get('id', '')
            combined_text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
            
            if not isRelevant(combined_text, config["BLOCKLIST"]):
                continue
            if not isZeroShotRelevant(combined_text, config["KEYWORDS"]):
                continue
            if isProbablyBot(post, posts_by_author):
                continue
            
            filtered.append(post)

        return filtered

    except Exception as e:
        print(f"[Reddit] API error for r/{subreddit}: {e}")
        return []

def fetchRedditPosts(coins, config):
    subreddit_map = {}
    for coin in coins:
        subreddit = known_subs.get(coin)
        if subreddit:
            subreddit_map[coin] = subreddit
    
    if not subreddit_map:
        print("[Reddit] No known subreddits found for these coins. Reddit collection will be skipped.")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_dir = os.path.join(base_dir, "logs/reddit_posts")
    os.makedirs(hist_dir, exist_ok=True)

    for coin, subreddit in subreddit_map.items():
        file_path = os.path.join(hist_dir, f"{coin.upper()}.csv")
        if os.path.exists(file_path):
            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)
            if datetime.now(timezone.utc) - last_modified < timedelta(minutes=15):
                print(f"[Reddit] Skipping {coin}, posts are already up to date.")
                continue

        posts = fetchSubreddit(subreddit, config)
        if posts is None:
            continue

        log(coin, posts)
        time.sleep(10)