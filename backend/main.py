import sys
import os
from fastapi import FastAPI, HTTPException
from backend.routers import product, user
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI()

app.include_router(product.router)
app.include_router(user.router)

@app.get("/")
async def root():
    return {"message": "API is running"}

