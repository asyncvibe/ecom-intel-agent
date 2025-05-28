import sys
import os
from fastapi import FastAPI, HTTPException
from backend.routers import product, user,sentiment
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
load_dotenv(override=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product.router)
app.include_router(user.router)
app.include_router(sentiment.router)
@app.get("/")
async def root():
    return {"message": "API is running"}

