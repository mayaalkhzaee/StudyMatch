from fastapi import FastAPI
from database import lifespan

app = FastAPI(lifespan=lifespan)