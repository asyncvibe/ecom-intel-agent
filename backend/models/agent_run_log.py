# models/agent_log.p
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from utils.mongo import PyObjectId
from bson import ObjectId
from typing import List, Literal, Optional
class AgentRunLogModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    agent: Literal["scraper", "analyzer", "summarizer"]
    input: str
    output: str
    status: Literal["success", "failed"]
    error: Optional[str]
    ran_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
