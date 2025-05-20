from typing import List, Dict
from pydantic import BaseModel
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from utils.mongo import PyObjectId
from bson import ObjectId
from typing import List, Literal, Optional
class ReviewModel(BaseModel):
    title: str
    body: str
    rating: float
    timestamp: Optional[datetime]

class ScrapedResultModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    platform: str
    url: str
    title: str
    price: Optional[float]
    specs: Dict[str, str]
    rating: Optional[float]
    reviews: List[ReviewModel]
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
