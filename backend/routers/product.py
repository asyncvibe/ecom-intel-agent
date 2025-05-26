from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from ..models.product import TrackedProductModel
from ..models.analysis import ProductAnalysis
from ..utils.mongo import PyObjectId
from bson import ObjectId
from typing import List, Literal, Dict
from datetime import datetime
from datetime import timezone
from ..db.database import products_collection,scraped_results_collection,reports_collection,sentiments_collection
# from scrapers.scraper_engine import ScraperEngine
from ..scrapers.scraper_engine import ScraperEngine
from ..agents.rag_agent import analyze_product

router = APIRouter(prefix="/products", tags=["Products"])

class ProductCreateRequest(BaseModel):
    name: str
    type: Literal["product", "brand", "category"]
    platforms: List[str]
    user_id: PyObjectId = Field(default_factory=PyObjectId)  # temporary default

# create a new tracked product
@router.post("/", response_model=TrackedProductModel)
def create_product(product: ProductCreateRequest):
    data = product.model_dump()
    data.update({
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "last_updated": datetime.now(timezone.utc),
    })
    result = products_collection.insert_one(data)
    created_product = products_collection.find_one({"_id": result.inserted_id})
    if created_product:
        return TrackedProductModel(**created_product)
    raise HTTPException(status_code=500, detail="Failed to create product")

# list all tracked products
@router.get("/", response_model=List[TrackedProductModel])
def list_products():
    products = products_collection.find()
    return [TrackedProductModel(**prod) for prod in products]

# get a tracked product by id
@router.get("/{product_id}", response_model=TrackedProductModel)
def get_product(product_id: str):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return TrackedProductModel(**product)

# update a tracked product
@router.put("/{product_id}", response_model=TrackedProductModel)
def update_product(product_id: str, update_data: ProductCreateRequest):
    update_dict = update_data.model_dump()
    update_dict["last_updated"] = datetime.now(timezone.utc)
    result = products_collection.update_one(
        {"_id": ObjectId(product_id)}, 
        {"$set": update_dict}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Product not found or unchanged")
    updated = products_collection.find_one({"_id": ObjectId(product_id)})
    if updated:
        return TrackedProductModel(**updated)
    raise HTTPException(status_code=404, detail="Product not found")

# delete a tracked product
@router.delete("/{product_id}")
def delete_product(product_id: str):
    result = products_collection.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# trigger scrapping for the tracked products
# @router.post("/{product_id}/scrape")
# async def scrape_product(product_id: str):
#     product = db["products"].find_one({"_id": ObjectId(product_id)})
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")

#     query = product["name"]
#     platforms = product.get("platforms", [])

#     results = []
#     for platform in platforms:
#         engine = ScraperEngine(platform, query)
#         result = await engine.run()
#         result.update({
#             "product_id": ObjectId(product_id),
#             "platform": platform,
#             "scraped_at": datetime.utcnow()
#         })
#         db["scraped_results"].insert_one(result)
#         results.append(result)

#     db["products"].update_one(
#         {"_id": ObjectId(product_id)},
#         {"$set": {"status": "scraped", "last_updated": datetime.utcnow()}}
#     )

#     return {"message": "Scraping complete", "results": results}

# Run scraper for the tracked products
@router.post("/{product_id}/scrape")
async def scrape_product(product_id: str):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    results = {}
    for platform in product.get("platforms", []):
        try:
            engine = ScraperEngine(platform, product["name"], product_id)
            result = await engine.run()
            results[platform] = result
        except Exception as e:
            results[platform] = {"error": str(e)}

    # Update product status
    products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {
            "status": "scraped",
            "last_updated": datetime.now(timezone.utc)
        }}
    )

    return {
        "product_id": product_id,
        "product_name": product["name"],
        "results": results
    }

@router.post("/{product_id}/scrape_competitors")
async def scrape_competitors(product_id: str, competitor_num: int = 3):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    results = {}
    for platform in product.get("platforms", []):
        try:
            engine = ScraperEngine(platform, product["name"], product_id, competitor_num)
            result = await engine.run()
            results[platform] = result
        except Exception as e:
            results[platform] = {"error": str(e)}
            # Update product status
    products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {
            "status": "scraped",
            "last_updated": datetime.now(timezone.utc)
        }}
    )

    return {
        "product_id": product_id,
        "product_name": product["name"],
        "results": results
    }
# asking agent about the product
class ProductQuestion(BaseModel):
    question: str

@router.post("/{product_id}/ask", response_model=ProductAnalysis)
async def ask_product_question(product_id: str, question: ProductQuestion):
    """Ask a question about product reviews using RAG"""
    try:
        # Verify product exists
        product = scraped_results_collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get analysis from RAG agent
        result = await analyze_product(question.question, product_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# unified report: summary from RAG + sentiment breakdown from scraped results + pricing information
@router.get("/unified_report/{product_id}")
async def get_unified_report(product_id: str):
    """Get a unified report for a product"""
    try:
    #   summary from RAG
        summary = reports_collection.find_one({"product_id": ObjectId(product_id)})
        sentiment = sentiments_collection.find_one({"product_id": ObjectId(product_id)})
        if not summary:
            raise HTTPException(status_code=404, detail="Product not found")
        from ..models.report import SummaryReportModel
        from ..models.sentiment import SentimentAnalysisModel
        summary_model = SummaryReportModel(**summary)
        if not sentiment:
            raise HTTPException(status_code=404, detail="Sentiment not found")
        sentiment_model = SentimentAnalysisModel(**sentiment)
        return {
            "summary": summary_model,
            "sentiment": sentiment_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   
    






