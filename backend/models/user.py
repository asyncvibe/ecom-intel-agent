from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from ..utils.mongo import PyObjectId
from bson import ObjectId


class SubscriptionModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    plan: str
    stripe_id: Optional[str] = None
    status: Optional[str] = None
    renewal_date: Optional[datetime]

class UserModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    password_hash: str
    name: Optional[str] = None
    role: str = "free"
    subscription: Optional[SubscriptionModel] = None
    team_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: Optional[datetime] = None

class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        
# from pydantic import BaseModel, EmailStr, Field
# from typing import Optional
# from datetime import datetime, timezone
# from bson import ObjectId
# from ..utils.mongo import PyObjectId

# class SubscriptionModel(BaseModel):
#     plan: str
#     stripe_id: Optional[str]
#     status: Optional[str]
#     renewal_date: Optional[datetime]

# class UserModel(BaseModel):
#     id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
#     email: EmailStr
#     password_hash: str
#     name: Optional[str]
#     role: str = "free"
#     subscription: Optional[SubscriptionModel]
#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
#     last_updated: Optional[datetime] = None
#     team_id: Optional[PyObjectId]

#     class Config:
#         populate_by_name = True  # Replaces allow_population_by_field_name
#         arbitrary_types_allowed = True
#         json_encoders = {
#             ObjectId: str,
#             PyObjectId: str
#         }
