from fastapi import APIRouter, Request, Depends, status, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import Annotated
from fastapi.encoders import jsonable_encoder

from auth import get_current_user

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    username: str
    email: str


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=20)
    email: EmailStr | None = Field(default=None)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[dict, Depends(get_current_user)]
):
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
    records = db["sessions"].find(
        {"enrolled_users": str(current_user["_id"])}
    )
    return [s async for s in records]


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: Request,
    user_data: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    encoded_data = jsonable_encoder(user_data)
    changes = {k: v for k, v in encoded_data.items() if v is not None}

    if not changes:
        return UserResponse(
            id=str(current_user["_id"]),
            username=current_user["username"],
            email=current_user["email"]
        )

    if "email" in changes and changes["email"] != current_user["email"]:
        if await db["users"].find_one({"email": changes["email"]}):
            raise HTTPException(status_code=400, detail="Email already registered")
            
    if "username" in changes and changes["username"] != current_user["username"]:
        if await db["users"].find_one({"username": changes["username"]}):
            raise HTTPException(status_code=400, detail="Username already taken")

    await db["users"].update_one({"_id": current_user["_id"]}, {"$set": changes})
    
    # update the host name on their sessions otherwise it shows the old username
    if "username" in changes and changes["username"] != current_user["username"]:
        await db["sessions"].update_many(
            {"host_id": str(current_user["_id"])},
            {"$set": {"host": changes["username"]}}
        )

    updated_user = await db["users"].find_one({"_id": current_user["_id"]})
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"]
    )


@router.delete("/me")
async def delete_me(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    user_id = current_user["_id"]

    # remove from any sessions they joined and fix the enrolled count
    await db["sessions"].update_many(
        {"enrolled_users": str(user_id)},
        {
            "$pull": {"enrolled_users": str(user_id)},
            "$inc": {"enrolled_count": -1}
        }
    )

    await db["sessions"].delete_many({"host_id": str(user_id)})

    await db["users"].delete_one({"_id": user_id})

    return {"message": "Account deleted successfully"}