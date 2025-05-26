"""
RAG (Retrieval-Augmented Generation) Agent for Product Analysis.
Analyzes product data using vector storage and LLM capabilities.
"""

import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone
from bson import ObjectId
import tiktoken
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.ui import Console

from ..utils.mongo import PyObjectId
from ..db.database import scraped_results_collection
from ..models.report import SummaryReportModel
# Load environment variables
load_dotenv()

# Setup paths and configurations
CHROMA_DB_PATH = Path("./data/chroma_db")
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

# Initialize vector memory
vector_memory = ChromaDBVectorMemory(
    config=PersistentChromaDBVectorMemoryConfig(
        collection_name="product_reviews",
        persistence_path=str(CHROMA_DB_PATH),
        k=3,
        score_threshold=0.4
    )
)

# Initialize LLM client and assistant
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
assistant = AssistantAgent(
    name="product_analyst",
    model_client=model_client,
    memory=[vector_memory],
    output_content_type=SummaryReportModel,
    system_message="""
    You are a Product Intelligence Agent for e-commerce sellers.

Your task is to analyze the given product data—including customer reviews, specifications, pricing information, and feature comparisons—and generate a structured and concise competitive summary. Your analysis should help sellers make better product, pricing, or marketing decisions.

Always think from the perspective of an e-commerce seller trying to understand:
- What do users like or dislike?
- What are the product’s strengths and weaknesses?
- Which features are missing compared to competitors?
- How is the pricing across platforms?
- Should this product be improved, marketed differently, or avoided?

Your output must be structured
Be objective. Avoid vague language. Use insights extracted from the reviews and product data only.
"""
)


def chunk_text(text: str, max_tokens: int = 400) -> List[str]:
    """Split text into chunks of approximately max_tokens length."""
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    return [tokenizer.decode(tokens[i:i + max_tokens]) for i in range(0, len(tokens), max_tokens)]

async def load_product_data(product_id: str) -> None:
    """Load product data into vector memory for analysis."""
    # Clear previous data
    await vector_memory.clear()
    
    # Get product data
    product = scraped_results_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise ValueError("No product data found")

    # Add specifications
    if specs := product.get("specifications"):
        await vector_memory.add(MemoryContent(
            content=str(specs),
            mime_type=MemoryMimeType.TEXT,
            metadata={"type": "specifications", "product_id": product_id}
        ))

    # Add metadata
    metadata = {
        "title": product.get("title", ""),
        "brand": product.get("brand", ""),
        "price": product.get("price", ""),
        "rating": product.get("rating", "")
    }
    await vector_memory.add(MemoryContent(
        content=str(metadata),
        mime_type=MemoryMimeType.TEXT,
        metadata={"type": "metadata", "product_id": product_id}
    ))

    # Add reviews
    if reviews := product.get("reviews"):
        for idx, review in enumerate(reviews):
            review_text = review.get("body", str(review)) if isinstance(review, dict) else str(review)
            for chunk_idx, chunk in enumerate(chunk_text(review_text)):
                await vector_memory.add(MemoryContent(
                    content=chunk,
                    mime_type=MemoryMimeType.TEXT,
                    metadata={
                        "type": "review",
                        "product_id": product_id,
                        "review_index": idx,
                        "chunk_index": chunk_idx
                    }
                ))

async def analyze_product(query: str, product_id: str) -> SummaryReportModel:
    """Analyze product data and return structured insights."""
    try:
        # Load product data into memory
        await load_product_data(product_id)

        # Get analysis from LLM
        result = await assistant.run(task=query)
        # Try to extract the content from the last message
        last_msg = result.messages[-1]
        content = getattr(last_msg, 'content', None)
        if content is None:
            # Try 'data' or fallback to the whole message
            content = getattr(last_msg, 'data', last_msg)
        print("🤖 LLM Response:", content)
        # If content is a dict, try to build SummaryReportModel
        if isinstance(content, dict):
            content = SummaryReportModel(**content)
        if not isinstance(content, SummaryReportModel):
            print("❌ Unexpected message format (not a StructuredMessage).")
            # Return a default model with minimal info to avoid type error
            from ..utils.mongo import PyObjectId
            # Only return if product_id is valid PyObjectId, else raise
            pid = PyObjectId(product_id)
            return SummaryReportModel(
                product_id=pid,
                buy_or_skip="neutral",
                pros=[],
                cons=[],
                feature_gaps=[],
                pricing_summary="",
                platform_recommendation="",
                generated_by="",
                generated_at=datetime.now(timezone.utc)
            )
       
        # Print structured fields
        print("🧠 product_id:", content.product_id)
        print("💰 buy_or_skip:", content.buy_or_skip)
        print("📝 pros:", content.pros)
        print("📝 cons:", content.cons)
        print("📝 feature_gaps:", content.feature_gaps)
        print("💰 pricing_summary:", content.pricing_summary)
        print("🔍 platform_recommendation:", content.platform_recommendation)
        print("🤖 generated_by:", content.generated_by)
        print("🕰️ generated_at:", content.generated_at)
        
        # Ensure product_id is a PyObjectId
        from ..utils.mongo import PyObjectId
        pid = getattr(content, 'product_id', None)
        if not isinstance(pid, PyObjectId):
            try:
                pid = PyObjectId(pid)
            except Exception:
                pid = PyObjectId(product_id)
                
        report = SummaryReportModel(
            product_id=pid,
            buy_or_skip=content.buy_or_skip,
            pros=content.pros,
            cons=content.cons,
            feature_gaps=content.feature_gaps,
            pricing_summary=content.pricing_summary,
            platform_recommendation=content.platform_recommendation,
            generated_by=content.generated_by,
            generated_at=getattr(content, 'generated_at', datetime.now(timezone.utc)),
            summary=getattr(content, 'summary', None),
            strengths=getattr(content, 'strengths', content.pros if hasattr(content, 'pros') else None),
            improvement_opportunities=getattr(content, 'improvement_opportunities', content.feature_gaps if hasattr(content, 'feature_gaps') else None),
            recommendations=getattr(content, 'recommendations', None)
        )
        # Save to reports_collection (upsert by product_id)
        from ..db.database import reports_collection
        reports_collection.replace_one(
            {"product_id": pid},
            report.model_dump(by_alias=True),
            upsert=True
        )
        return report
        
    except Exception as e:
        raise Exception(f"error: {str(e)}")
    finally:
        await model_client.close()

# --- End of file ---