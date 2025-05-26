from typing import List, Dict
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..utils.mongo import PyObjectId
from bson import ObjectId

class ReviewModel(BaseModel):
    title: str
    body: str
    rating: float
    timestamp: Optional[datetime]

class ProductModel(BaseModel):
    url: str
    title: str
    price: Optional[float]
    specifications: Dict[str, str]
    rating: Optional[float]
    reviews: List[ReviewModel]

class ScrapedCompetitorsModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    platform: str
    products: List[ProductModel]  # List of products
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
