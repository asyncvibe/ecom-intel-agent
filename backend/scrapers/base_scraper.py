# scrapers/base_scraper.py
from abc import ABC, abstractmethod
# this is the base class for scrapers; enforces the scrape method to be implemented; used by AmazonScraper and FlipkartScraper; if we want to add a new scraper, we can inherit from this class and implement scrape method: it also initializes the query attribute for all scrapers, so that we don't have to pass it as an argument to the scrape method in each scraper
class BaseScraper(ABC):
    def __init__(self, query: str):
        self.query = query

    @abstractmethod
    async def scrape(self) -> dict:
        pass
