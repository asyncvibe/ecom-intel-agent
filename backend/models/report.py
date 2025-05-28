from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Literal, Optional
from ..utils.mongo import PyObjectId
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
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    improvement_opportunities: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
