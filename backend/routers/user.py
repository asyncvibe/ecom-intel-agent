from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
from ..db.database import users_collection
from ..models.user import UserModel, SubscriptionModel
from ..utils.mongo import PyObjectId
from ..utils.auth import hash_password, create_access_token, get_current_user, Token, verify_password

router = APIRouter(prefix="/user", tags=["User"])

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str  # Changed to plain password for hashing
    name: Optional[str] = None
    role: str = "free"
    subscription: Optional[SubscriptionModel] = None
    team_id: Optional[PyObjectId] = None

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/create", response_model=UserModel)
def create_user(user: UserCreateRequest):
    # Check for existing user with the same email
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    # Hash the password
    hashed_password = hash_password(user.password)
    
    # Prepare data for insertion
    data = user.model_dump(exclude={"password"})
    data["password_hash"] = hashed_password
    data.update({
        "_id": PyObjectId(),
        "created_at": datetime.now(timezone.utc),
        "last_updated": None
    })
    
    # Insert into MongoDB
    result = users_collection.insert_one(data)
    created_user = users_collection.find_one({"_id": result.inserted_id})
    
    if created_user:
        # Ensure ObjectId fields are strings for Pydantic
        created_user["_id"] = str(created_user["_id"])
        if created_user.get("team_id"):
            created_user["team_id"] = str(created_user["team_id"])
        return UserModel(**created_user)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

# Login
@router.post("/login", response_model=Token)
def login_user(login: UserLoginRequest):
    user = users_collection.find_one({"email": login.email})
    if not user or not verify_password(login.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    access_token = create_access_token(data={"user_id": str(user["_id"]), "email": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}
# find all users
@router.get("/", response_model=List[UserModel])
def list_users(current_user: UserModel = Depends(get_current_user)):
    users = users_collection.find()
    return [UserModel(**user) for user in users]
# find a user by id
@router.get("/{user_id}", response_model=UserModel)
def get_user(user_id: str, current_user: UserModel = Depends(get_current_user)):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserModel(**user)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
# update a user
@router.put("/{user_id}", response_model=UserModel)
def update_user(user_id: str, update_data: UserCreateRequest, current_user: UserModel = Depends(get_current_user)):
    try:
        # Check for email conflict with other users
        if update_data.email and users_collection.find_one({"email": update_data.email, "_id": {"$ne": ObjectId(user_id)}}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        # Hash password if provided
        update_dict = update_data.model_dump(exclude_unset=True)
        if "password" in update_dict:
            update_dict["password_hash"] = hash_password(update_dict.pop("password"))
        update_dict["last_updated"] = datetime.now(timezone.utc)
        
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or unchanged")
        
        updated_user = users_collection.find_one({"_id": ObjectId(user_id)})
        if updated_user:
            return UserModel(**updated_user)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
# delete a user
@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: UserModel = Depends(get_current_user)):
    try:
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return {"message": "User deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
