from fastapi import APIRouter, Request, Depends, status
from pydantic import BaseModel
from typing import Annotated

from auth import get_current_user

router = APIRouter()

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"]
    )

@router.get("/me/sessions")
async def get_my_sessions(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    records = db["sessions"].find({"host_id": str(current_user["_id"])})
    return [s async for s in records]

@router.get("/me/joined")
async def get_joined_sessions(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    records = db["sessions"].find({"enrolled_users": str(current_user["_id"])})
    return [s async for s in records]
