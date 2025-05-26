# scrapers/scraper_engine.py

from .amazon import scrape_product_amazon
from .flipkart import scrape_product_flipkart
from .ebay import scrape_product_ebay
from datetime import datetime,timezone

from bson import ObjectId
from ..db.database import scraped_results_collection, agent_run_log_collection, scraped_competitors_collection

class ScraperEngine:
    def __init__(self, platform: str, query: str, product_id: str, competitor_num: int = 1):
        self.platform = platform
        self.query = query
        self.product_id = ObjectId(product_id)
        self.competitor_num = competitor_num

    async def run(self):
        results = None
        try:
            if self.platform == "amazon":
                results = await scrape_product_amazon(self.query, self.competitor_num)
            elif self.platform == "flipkart":
                results = await scrape_product_flipkart(self.query, self.competitor_num)
            elif self.platform == "ebay":
                results = await scrape_product_ebay(self.query, self.competitor_num)
            else:
                return {"error": "Unsupported platform"}

            if results:
                # Ensure results is a list
                if not isinstance(results, list):
                    results = [results]

                # If only one product, save to scraped_results_collection
                if len(results) == 1:
                    scraped_results_collection.insert_one({
                        "product_id": self.product_id,
                        "platform": self.platform,
                        "url": results[0].get("url"),
                        "title": results[0].get("title"),
                        "brand": results[0].get("brand"),
                        "price": results[0].get("price"),
                        "rating": results[0].get("rating"),
                        "reviews": results[0].get("reviews", []),
                        "specifications": results[0].get("specifications", {}),
                        "scraped_at": datetime.now(timezone.utc)
                    })
                # If multiple products, save to scraped_competitors_collection
                else:
                    # Prepare products list
                    products = []
                    for result in results:
                        products.append({
                            "url": result.get("url"),
                            "title": result.get("title"),
                            "price": result.get("price"),
                            "specifications": result.get("specifications", {}),
                            "rating": result.get("rating"),
                            "reviews": result.get("reviews", [])
                        })
                    
                    # Save all products under one document
                    scraped_competitors_collection.insert_one({
                        "product_id": self.product_id,
                        "platform": self.platform,
                        "products": products,
                        "scraped_at": datetime.now(timezone.utc)
                    })

                # Log result
                agent_run_log_collection.insert_one({
                    "platform": self.platform,
                    "query": self.query,
                    "result": results,
                    "status": "success" if results and not any("error" in r for r in results) else "failed",
                    "ran_at": datetime.now(timezone.utc)
                })

                # Return all results
                return results

        except Exception as e:
            error_result = {"error": str(e)}
            # Log error
            agent_run_log_collection.insert_one({
                "platform": self.platform,
                "query": self.query,
                "result": error_result,
                "status": "failed",
                "ran_at": datetime.now(timezone.utc)
            })
            return error_result
