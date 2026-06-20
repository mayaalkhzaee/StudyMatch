import uuid
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
    db = request.app.database
    
    # Create new session object combining user input and host data
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
    session_data: SessionCreate, 
    current_user: Annotated[dict, Depends(get_current_user)]
):
    db = request.app.database
    session = await db["sessions"].find_one({"_id": id})
    
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    if session["host_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        
    # Extract changes and update
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
        
    # Ensure only the host can delete
    if session["host_id"] != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        
    delete_result = await db["sessions"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return {"message": "Session deleted successfully"}
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")