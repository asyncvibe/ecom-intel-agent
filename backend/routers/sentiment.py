from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.sentiment import SentimentAnalysisModel
from ..utils.mongo import PyObjectId
from bson import ObjectId
from typing import List, Dict
from datetime import datetime, timezone
from ..db.database import scraped_results_collection, sentiments_collection
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
import re

nltk.download('vader_lexicon')
analyzer = SentimentIntensityAnalyzer()

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])

def analyze_sentiment(text):
    scores = analyzer.polarity_scores(text)
    return scores

def extract_keywords(text, n=5):
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()
    stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'of', 'from'])
    words = [word for word in words if word not in stop_words]
    word_freq = Counter(words)
    return [word for word, _ in word_freq.most_common(n)]

@router.post("/{scraped_id}", response_model=SentimentAnalysisModel)
async def get_sentiment(scraped_id: str):
    try:
        scraped_result = scraped_results_collection.find_one({"_id": ObjectId(scraped_id)})
        if not scraped_result:
            raise HTTPException(status_code=404, detail="Scraped result not found")

        reviews = scraped_result.get("reviews", [])
        if not reviews:
            raise HTTPException(status_code=404, detail="No reviews found in the scraped result")

        sentiment_scores = []
        for review in reviews:
            scores = analyze_sentiment(review)
            sentiment_scores.append({
                "text": review,
                "scores": scores
            })

        positive_reviews = [s["text"] for s in sentiment_scores if s["scores"]["compound"] > 0.05]
        negative_reviews = [s["text"] for s in sentiment_scores if s["scores"]["compound"] < -0.05]

        sentiment_result = {
            "product_id": scraped_result["product_id"],
            "platform": scraped_result["platform"],
            "summary": {
                "positive": len(positive_reviews),
                "negative": len(negative_reviews),
                "neutral": len(sentiment_scores) - len(positive_reviews) - len(negative_reviews)
            },
            "keywords": {
                "positive": extract_keywords(" ".join(positive_reviews)),
                "negative": extract_keywords(" ".join(negative_reviews))
            },
            "top_positive_review": max(positive_reviews, key=lambda text: analyzer.polarity_scores(text)["compound"], default=""),
            "top_negative_review": min(negative_reviews, key=lambda text: analyzer.polarity_scores(text)["compound"], default=""),
            "processed_at": datetime.now(timezone.utc)
        }

        # Upsert (update if exists, otherwise insert)
        sentiments_collection.replace_one(
            {"product_id": scraped_result["product_id"], "platform": scraped_result["platform"]},
            sentiment_result,
            upsert=True
        )

        return SentimentAnalysisModel(**sentiment_result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get a sentiment analysis
# @router.get("/{product_id}", response_model=SentimentAnalysisModel)
# def get_sentiment(product_id: str):
#     sentiment = scraped_results_collection.find_one({"product_id": ObjectId(product_id)})
#     if not sentiment:
#         raise HTTPException(status_code=404, detail="Sentiment not found")
#     return SentimentAnalysisModel(**sentiment)