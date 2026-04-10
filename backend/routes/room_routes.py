# backend/routes/room_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models import RoomCreate, RoomResponse, ApiResponse
from backend.database import db
from backend.auth import security, decode_token

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])

@router.get("/", response_model=List[RoomResponse])
async def get_all_rooms(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all rooms"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    query = "SELECT room_no, capacity FROM room_table"
    results = db.execute_query(query)
    
    return results or []

@router.post("/", response_model=ApiResponse)
async def create_room(
    room: RoomCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new room (Admin only)"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = "INSERT INTO room_table (room_no, capacity) VALUES (%s, %s)"
    result = db.execute_insert(query, (room.room_no, room.capacity))
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create room")
    
    return ApiResponse(success=True, message="Room created successfully")

@router.delete("/{room_no}", response_model=ApiResponse)
async def delete_room(
    room_no: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a room (Admin only)"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = "DELETE FROM room_table WHERE room_no = %s"
    success = db.execute_update(query, (room_no,))
    
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return ApiResponse(success=True, message="Room deleted successfully")