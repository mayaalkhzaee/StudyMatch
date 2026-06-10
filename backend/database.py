from contextlib import asynccontextmanager
from dotenv import dotenv_values
from pymongo import AsyncMongoClient
from fastapi import FastAPI

config = dotenv_values("../.env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncMongoClient(config["DB_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to MongoDB")
    yield
    app.mongodb_client.close()