import uuid
from datetime import date as Date, timezone, datetime
from enum import Enum
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field, ConfigDict
from fastapi.encoders import jsonable_encoder
from typing import Annotated

from auth import get_current_user

router = APIRouter()


class SessionType(str, Enum):
    online = "online"
    in_person = "in-person"


class SessionCreate(BaseModel):
    course: str = Field(...)
    type: SessionType = Field(...)
    location: str = Field(...)
    date: Date = Field(...)
    time: str = Field(...)
    capacity: int = Field(..., gt=0)


class SessionUpdate(BaseModel):
    course: str | None = Field(default=None)
    type: SessionType | None = Field(default=None)
    location: str | None = Field(default=None)
    date: Date | None = Field(default=None)
    time: str | None = Field(default=None)
    capacity: int | None = Field(default=None, gt=0)


class SessionResponse(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), alias="_id"
    )
    course: str
    host: str
    host_id: str
    type: SessionType
    location: str
    date: Date
    time: str
    capacity: int
    enrolled_count: int = 0
    enrolled_users: list[str] = []

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


@router.get("", response_model=list[SessionResponse])
async def get_all_sessions(request: Request):
    db = request.app.database
    records = db["sessions"].find()
    sessions = [i async for i in records]
    return sessions


@router.get("/recommended", response_model=list[SessionResponse])
async def get_recommended_sessions(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    joined_ids = current_user.get("joined_session_ids", [])

    joined_cursor = db["sessions"].find({"_id": {"$in": joined_ids}})
    joined_courses = list(set(
        [s["course"] async for s in joined_cursor if "course" in s]
    ))

    if not joined_courses:
        return []

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # only recommend sessions in the same courses that the are not yet joined and are upcoming and not full
    query = {
        "course": {"$in": joined_courses},
        "_id": {"$nin": joined_ids},
        "host_id": {"$ne": str(current_user["_id"])},
        "date": {"$gte": today_str},
        "$expr": {"$lt": ["$enrolled_count", "$capacity"]}
    }
    
    recommended_cursor = db["sessions"].find(query)
    return [s async for s in recommended_cursor]

@router.get("/{id}", response_model=SessionResponse)
async def get_session(id: str, request: Request):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionResponse
)
async def create_session(
    request: Request,
    session_data: SessionCreate,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    if session_data.date < Date.today():
        raise HTTPException(
            status_code=400,
            detail="Session date cannot be in the past."
        )
    db = request.app.database
    new_session = SessionResponse(
        course=session_data.course,
        type=session_data.type,
        location=session_data.location,
        date=session_data.date,
        time=session_data.time,
        capacity=session_data.capacity,
        host=current_user["username"],
        host_id=str(current_user["_id"])
    )
    jsession = jsonable_encoder(new_session)
    await db["sessions"].insert_one(jsession)
    return jsession


@router.put("/{id}", response_model=SessionResponse)
async def update_session(
    id: str,
    request: Request,
    session_data: SessionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session["host_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
    )
    encoded_data = jsonable_encoder(session_data)
    changes = {
        k: v for k, v in encoded_data.items()
        if v is not None
    }
    if len(changes) > 0:
        await db["sessions"].update_one({"_id": id}, {"$set": changes})
    updated_session = await db["sessions"].find_one({"_id": id})
    return updated_session


@router.delete("/{id}")
async def delete_session(
    id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session["host_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    delete_result = await db["sessions"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return {"message": "Session deleted successfully"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Session not found"
    )


@router.post("/{id}/join")
async def join_session(
    id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    enrolled_users = session.get("enrolled_users", [])
    if current_user["_id"] in enrolled_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already joined this session"
        )
    enrolled_count = session.get("enrolled_count", 0)
    if enrolled_count >= session.get("capacity", 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is full"
        )
    enrolled_users.append(str(current_user["_id"]))
    new_count = enrolled_count + 1
    await db["sessions"].update_one(
        {"_id": id},
        {"$set": {
            "enrolled_users": enrolled_users,
            "enrolled_count": new_count
        }}
    )
    # update the user's joined list too so /me/joined stays in sync
    joined_sessions = current_user.get("joined_session_ids", [])
    joined_sessions.append(id)
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"joined_session_ids": joined_sessions}}
    )
    return {
        "message": "Successfully joined session",
        "enrolled_count": new_count
    }


@router.post("/{id}/leave")
async def leave_session(
    id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    enrolled_users = session.get("enrolled_users", [])
    if str(current_user["_id"]) not in enrolled_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not enrolled in this session"
        )
    enrolled_users.remove(str(current_user["_id"]))
    new_count = session.get("enrolled_count", 1) - 1
    await db["sessions"].update_one(
        {"_id": id},
        {"$set": {
            "enrolled_users": enrolled_users,
            "enrolled_count": new_count
        }}
    )
    joined_sessions = current_user.get("joined_session_ids", [])
    if id in joined_sessions:
        joined_sessions.remove(id)
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"joined_session_ids": joined_sessions}}
    )
    return {
        "message": "Successfully left session",
        "enrolled_count": new_count
    }
