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
# -------------------------- SUMMARY REPORT ROUTES --------------------------
report_router = APIRouter(prefix="/summary", tags=["Summary Reports"])

@report_router.get("/{product_id}", response_model=SummaryReportModel)
def get_summary(product_id: str):
    report = db["summaries"].find_one({"product_id": ObjectId(product_id)})
    if not report:
        raise HTTPException(status_code=404, detail="Summary not found")
    return SummaryReportModel(**report)