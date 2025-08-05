from transformers import pipeline

finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")

def getSentimentScore(text):
    try:
        result = finbert(text[:512])[0]  # Limit to 512 tokens
        label = result["label"]
        score = result["score"]

        # Normalize: convert to [-1, 1]
        if label == "positive":
            return score
        elif label == "negative":
            return -score
        else: 
            return 0.0
    except Exception as e:
        print(f"FinBERT sentiment error: {e}")
        return 0.0
    