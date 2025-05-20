from typing import Optional
from pymongo import MongoClient, errors
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

MONGO_URI: str = os.getenv("MONGO_URI", "")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

DB_NAME: str = os.getenv("DATABASE_NAME", "")
if not DB_NAME:
    raise ValueError("DATABASE_NAME environment variable is not set")

try:
    client: MongoClient = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)  # 3s timeout
    client.server_info()  # Forces connection on init
    print("✅ MongoDB connection established.")
except errors.ServerSelectionTimeoutError as err:
    print("❌ Failed to connect to MongoDB:", err)
    raise SystemExit(err)

db: Database = client[DB_NAME]
products_collection: Collection = db["products"]
users_collection: Collection = db["users"]
reports_collection: Collection = db["reports"]
summaries_collection: Collection = db["summaries"]
sentiments_collection: Collection = db["sentiments"]
scraped_results_collection: Collection = db["scraped_results"]
