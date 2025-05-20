# routers/product.py
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from models.product import TrackedProductModel
from models.scraped_result import ScrapedResultModel
from models.sentiment import SentimentAnalysisModel
from models.report import SummaryReportModel
from utils.mongo import PyObjectId
from bson import ObjectId
from typing import List
from datetime import datetime
from database import db  # Assuming db["products"] etc. are your collections
# -------------------------- SENTIMENT ANALYSIS ROUTES --------------------------
sentiment_router = APIRouter(prefix="/sentiment", tags=["Sentiment"])

@sentiment_router.get("/{product_id}", response_model=SentimentAnalysisModel)
def get_sentiment(product_id: str):
    sentiment = db["sentiments"].find_one({"product_id": ObjectId(product_id)})
    if not sentiment:
        raise HTTPException(status_code=404, detail="Sentiment not found")
    return SentimentAnalysisModel(**sentiment)