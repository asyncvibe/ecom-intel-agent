from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from ..models.product import TrackedProductModel
from ..utils.mongo import PyObjectId
from bson import ObjectId
from typing import List, Literal
from datetime import datetime
from datetime import timezone
from ..db.database import products_collection

router = APIRouter(prefix="/products", tags=["Products"])

class ProductCreateRequest(BaseModel):
    name: str
    type: Literal["product", "brand", "category"]
    platforms: List[str]
    user_id: PyObjectId = Field(default_factory=PyObjectId)  # temporary default

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

@router.get("/", response_model=List[TrackedProductModel])
def list_products():
    products = products_collection.find()
    return [TrackedProductModel(**prod) for prod in products]

@router.get("/{product_id}", response_model=TrackedProductModel)
def get_product(product_id: str):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return TrackedProductModel(**product)

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

@router.delete("/{product_id}")
def delete_product(product_id: str):
    result = products_collection.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}






