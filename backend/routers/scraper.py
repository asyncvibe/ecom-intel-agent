# triggers scraper engine
from fastapi import APIRouter, HTTPException
from scrapers.scraper_engine import ScraperEngine
router = APIRouter(prefix="/scrape", tags=["Scraper"])

@router.post("/{platform}")
async def trigger_scrape(platform: str, query: str):
    engine = ScraperEngine(platform, query)
    result = await engine.run()
    return result
