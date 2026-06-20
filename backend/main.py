from fastapi import FastAPI, Request, HTTPException
from database import lifespan
from auth import router as auth_router

app = FastAPI(lifespan=lifespan)

# Include the auth router with the /auth prefix
app.include_router(auth_router, prefix="/auth")

@app.get("/health")
async def health_check(request: Request):
    try:
        # Ping the database to confirm the connection is active
        await request.app.mongodb_client.admin.command('ping')
        return {
            "status": "ok", 
            "message": "API is running and successfully connected to MongoDB via PyMongo"
        }
    except Exception as e:
        # If the ping fails, return a 503 Service Unavailable error
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")