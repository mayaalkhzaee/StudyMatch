import uuid
from datetime import datetime, timezone, date
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field, ConfigDict
from fastapi.encoders import jsonable_encoder
from typing import Annotated

# Import the dependency from our auth module
from auth import get_current_user

# Create the router for sessions
router = APIRouter()

# --- Pydantic Models ---
class SessionCreate(BaseModel):
    course: str
    type: str
    location: str
    date: str
    time: str
    capacity: int

class SessionResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    course: str
    host: str
    host_id: str
    type: str
    location: str
    date: str
    time: str
    capacity: int
    enrolled_count: int = 0
    enrolled_users: list[str] = []

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

# --- Endpoints ---

@router.get("", response_model=list[SessionResponse])
async def get_all_sessions(request: Request):
    db = request.app.database
    records = db["sessions"].find()
    sessions = [i async for i in records]
    return sessions

@router.get("/{id}", response_model=SessionResponse)
async def get_session(id: str, request: Request):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
async def create_session(
    request: Request, 
    session_data: SessionCreate, 
    current_user: Annotated[dict, Depends(get_current_user)]
):
    try:
        session_date = date.fromisoformat(session_data.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if session_date < date.today():
        raise HTTPException(status_code=400, detail="Session date cannot be in the past.")

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
    
    # Encode for MongoDB 
    jsession = jsonable_encoder(new_session)
    await db["sessions"].insert_one(jsession)
    
    return jsession

class SessionUpdate(BaseModel):
    course: str | None = None
    type: str | None = None
    location: str | None = None
    date: str | None = None
    time: str | None = None
    capacity: int | None = None

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    if session["host_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        
    changes = {k: v for k, v in session_data.model_dump().items() if v is not None}
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    if session["host_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        
    delete_result = await db["sessions"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return {"message": "Session deleted successfully"}
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

@router.post("/{id}/join")
async def join_session(
    id: str, 
    request: Request, 
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    enrolled_users = session.get("enrolled_users", [])
    if current_user["_id"] in enrolled_users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already joined this session")
        
    enrolled_count = session.get("enrolled_count", 0)
    if enrolled_count >= session.get("capacity", 0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is full")
    
    enrolled_users.append(str(current_user["_id"]))
    new_count = enrolled_count + 1
    
    await db["sessions"].update_one(
        {"_id": id}, 
        {"$set": {"enrolled_users": enrolled_users, "enrolled_count": new_count}}
    )
    
    joined_sessions = current_user.get("joined_session_ids", [])
    joined_sessions.append(id)
    
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"joined_session_ids": joined_sessions}}
    )
    
    enrollment = {
        "_id": str(uuid.uuid4()),
        "user_id": current_user["_id"],
        "session_id": id,
        "enrolled_at": datetime.now(timezone.utc).isoformat()
    }
    await db["enrollments"].insert_one(enrollment)
    
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    enrolled_users = session.get("enrolled_users", [])
    if str(current_user["_id"]) not in enrolled_users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not enrolled in this session")
        
    enrolled_users.remove(str(current_user["_id"]))
    new_count = session.get("enrolled_count", 1) - 1
    
    await db["sessions"].update_one(
        {"_id": id}, 
        {"$set": {"enrolled_users": enrolled_users, "enrolled_count": new_count}}
    )
    
    joined_sessions = current_user.get("joined_session_ids", [])
    if id in joined_sessions:
        joined_sessions.remove(id)
        
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"joined_session_ids": joined_sessions}}
    )
    
    await db["enrollments"].delete_one({
        "user_id": current_user["_id"],
        "session_id": id
    })
    
    return {
        "message": "Successfully left session",
        "enrolled_count": new_count
    }