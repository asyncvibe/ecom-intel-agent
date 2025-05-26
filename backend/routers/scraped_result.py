# routers/product.py
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..models.product import TrackedProductModel
from ..models.scraped_result import ScrapedResultModel
from ..models.sentiment import SentimentAnalysisModel
from ..models.report import SummaryReportModel
from ..utils.mongo import PyObjectId
from bson import ObjectId
from typing import List
from datetime import datetime
from ..db.database import scraped_results_collection, scraped_competitors_collection

scraped_router = APIRouter(prefix="/scraped", tags=["Scraped Results"])

@scraped_router.get("/{product_id}", response_model=List[ScrapedResultModel])
def get_scraped_data(product_id: str):
    results = scraped_results_collection.find({"product_id": ObjectId(product_id)})
    return [ScrapedResultModel(**res) for res in results]