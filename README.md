# E-commerce Intelligence Agent

A FastAPI-based service for tracking and analyzing e-commerce products.

## Features Implemented

- **Product Tracking**: Add, update, delete, and list tracked products with support for multiple platforms.
- **Automated Product Scraping**: Scrape product data and competitor data from supported e-commerce platforms.
- **RAG (Retrieval-Augmented Generation) Analysis**: Uses LLMs to generate structured product analysis and recommendations based on reviews, specifications, and pricing.
- **Sentiment Analysis**: Extracts sentiment breakdown and keywords from product reviews using NLP techniques.
- **Summary Reports**: Generates and stores detailed summary reports for each product, including strengths, weaknesses, feature gaps, and platform recommendations.
- **Unified API Response**: Provides a unified API endpoint to retrieve both the summary report and sentiment analysis for a product in a single response.
- **MongoDB Integration**: All data is stored and managed in MongoDB collections for products, reports, summaries, and sentiments.
- **Extensible Design**: Modular backend structure for easy extension and maintenance.

## API Endpoints (Highlights)

- `/products/` - CRUD operations for tracked products
- `/products/{product_id}/scrape` - Scrape product data
- `/products/{product_id}/scrape_competitors` - Scrape competitor data
- `/products/{product_id}/ask` - Get LLM-based product analysis
- `/products/unified_report/{product_id}` - Get combined summary and sentiment analysis

## Tech Stack

- FastAPI
- MongoDB
- Pydantic
- OpenAI LLMs (RAG)
- ChromaDB (vector storage)

---

For setup and usage instructions, see the code and comments in the respective modules.
