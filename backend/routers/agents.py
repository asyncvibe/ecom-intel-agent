from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.scraper import query_product_agent
router = APIRouter(prefix="/agents", tags=["Agents"])

class ProductQuery(BaseModel):
    query: str
    
@router.post("/ask")
async def ask_agent(data: ProductQuery):
    try:
        result = await query_product_agent(data.query)
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))