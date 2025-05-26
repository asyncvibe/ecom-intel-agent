from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from ..utils.mongo import PyObjectId

class ProductAnalysis(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    summary: str = Field(..., description="Brief overview of the product's reception and experience")
    strengths: List[str] = Field(..., description="List of customer-loved aspects or standout features")
    improvement_opportunities: List[str] = Field(..., description="List of weak spots, missing features, or areas not mentioned in reviews")
    recommendations: List[str] = Field(..., description="List of suggestions for the seller to add, improve, or emphasize")
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "summary": "The product has received positive feedback for its core features...",
                "strengths": [
                    "Excellent noise cancellation",
                    "Superior comfort for extended wear"
                ],
                "improvement_opportunities": [
                    "Limited multi-device connectivity",
                    "No water resistance rating"
                ],
                "recommendations": [
                    "Add IPX4 water resistance",
                    "Improve multi-device switching capabilities"
                ]
            }
        } 