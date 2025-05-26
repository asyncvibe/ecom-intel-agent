from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime,timezone
from ..utils.mongo import PyObjectId
from bson import ObjectId
from typing import List, Literal, Optional, Dict
class SentimentAnalysisModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    platform: str
    summary: Dict[str, int]  # {"positive": 20, "negative": 5, ...}
    keywords: Dict[str, List[str]]
    top_positive_review: str
    top_negative_review: str
    processed_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
