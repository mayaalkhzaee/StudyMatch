from fastapi import FastAPI, Request, HTTPException
from database import lifespan

app = FastAPI(lifespan=lifespan)

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