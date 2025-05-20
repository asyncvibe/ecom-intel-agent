from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from passlib.context import CryptContext
from ..db.database import users_collection
from ..models.user import UserModel
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Replace with a secure key in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str
    email: str

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        if user_id is None or email is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, email=email)
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"_id": ObjectId(token_data.user_id), "email": token_data.email})
    if user is None:
        raise credentials_exception
    return UserModel(**user)
