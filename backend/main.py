import uuid
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from database import lifespan
from pwdlib import PasswordHash

app = FastAPI(lifespan=lifespan)
password_hash = PasswordHash.recommended()

def get_password_hash(password: str):
    return password_hash.hash(password)

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class UserRegisterResponse(BaseModel):
    id: str
    username: str
    email: str
    
class UserBase(BaseModel):
    # Use a lambda to ensure the ID is a string, and alias="_id" for MongoDB compatibility
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    username: str
    email: EmailStr
    joined_session_ids: list[str] = []

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class NewUser(UserBase):
    password: str

class DBUser(UserBase):
    hashed_password: str

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
    
@app.post("/auth/register", status_code=status.HTTP_201_CREATED, response_model=UserRegisterResponse)
async def register_user(user: UserRegisterRequest, request: Request):
    db = request.app.database
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "joined_session_ids": []
    }
    result = await db.users.insert_one(new_user)
    return UserRegisterResponse(id=str(result.inserted_id), username=user.username, email=user.email)