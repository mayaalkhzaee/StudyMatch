from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import lifespan

# Import our routers
from auth import router as auth_router
from sessions import router as sessions_router
from users import router as users_router

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(sessions_router, prefix="/sessions")
app.include_router(users_router, prefix="/users")

@app.get("/health")
async def health_check(request: Request):
    try:
        await request.app.mongodb_client.admin.command('ping')
        return {
            "status": "ok", 
            "message": "API is running and successfully connected to MongoDB via PyMongo"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")