from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from ..utils.mongo import PyObjectId

class ProductAnalysis(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    summary: str = Field(..., description="Brief overview of the product's reception and experience")
    strengths: List[str] = Field(..., description="List of customer-loved aspects or standout features")
    improvement_opportunities: List[str] = Field(..., description="List of weak spots, missing features, or areas not mentioned in reviews")
    recommendations: List[str] = Field(..., description="List of suggestions for the seller to add, improve, or emphasize")
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )