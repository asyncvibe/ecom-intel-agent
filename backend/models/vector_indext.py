from pydantic import BaseModel, EmailStr, Field
from typing import Optional,List
from datetime import datetime
from utils.mongo import PyObjectId
from bson import ObjectId
class VectorIndexModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    chunk_id: str
    text: str
    source: str  # review, spec, pricing, etc.
    embedding: List[float]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
