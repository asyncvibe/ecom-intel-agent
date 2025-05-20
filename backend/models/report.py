# models/report.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from typing import List, Literal, Optional
from utils.mongo import PyObjectId
class SummaryReportModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    buy_or_skip: Literal["buy", "skip", "neutral"]
    pros: List[str]
    cons: List[str]
    feature_gaps: List[str]
    pricing_summary: str
    platform_recommendation: str
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
