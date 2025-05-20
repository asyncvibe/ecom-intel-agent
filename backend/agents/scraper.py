import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

agent = AssistantAgent(
    name="Product_Agent",
    model_client=model_client,
    system_message="Answer product-related queries using your tools and knowledge."
)

async def query_product_agent(query: str) -> str:
    print(f"Query: {query}")
    response = await agent.run(task=query)
    return response.messages[-1].content