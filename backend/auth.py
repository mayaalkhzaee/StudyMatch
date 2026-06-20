import uuid
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from typing import Annotated
from dotenv import dotenv_values

config = dotenv_values("../.env")
JWT_SECRET = config["JWT_SECRET"]

router = APIRouter()

password_hash = PasswordHash([BcryptHasher()])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_password_hash(password: str):
    return password_hash.hash(password)

def verify_password_hash(plaintext: str, hashedpass: str):
    return password_hash.verify(plaintext, hashedpass)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=120)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

# --- Pydantic Models ---
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class UserRegisterResponse(BaseModel):
    id: str
    username: str
    email: str

class UserBase(BaseModel):
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

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# --- Dependencies ---
async def get_current_user(req: Request, token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        # Decode the token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        email: str = payload.get("user")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token payload"
            )
    except Exception:
        # Catching generic JWT exceptions
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token is missing or invalid"
        )
    
    # Fetch the user from MongoDB
    user = await req.app.database["users"].find_one({"email": email})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    return user


# --- Endpoints ---
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRegisterResponse)
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

@router.post("/login", response_model=TokenResponse)
async def login(req: Request, data: LoginRequest):
    db = req.app.database
    collection = db["users"]
    
    # Find user by email
    user = await collection.find_one({"email": data.email})
    
    # Verify user exists AND password hash matches
    if not user or not verify_password_hash(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Issue JWT Token 
    token = create_access_token({"user": user["email"]})
    return TokenResponse(access_token=token, token_type="bearer")