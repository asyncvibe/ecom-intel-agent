from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Optional
from datetime import datetime, timezone
from bson import ObjectId
from ..utils.mongo import PyObjectId

class TrackedProductModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    name: str
    type: Literal["product", "brand", "category"]
    platforms: List[str]
    status: Literal["pending", "scraped", "analyzed"] = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: Optional[datetime] = None
