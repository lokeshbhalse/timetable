# backend/routes/slot_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models import SlotCreate, SlotResponse, ApiResponse
from backend.database import db
from backend.auth import security, decode_token

router = APIRouter(prefix="/api/slots", tags=["Slots"])

@router.get("/", response_model=List[SlotResponse])
async def get_all_slots(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all time slots from slot_table"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    query = "SELECT slot_id, slot_name, day, time_from, till_time FROM slot_table ORDER BY slot_id"
    results = db.execute_query(query)
    
    return results or []

@router.post("/", response_model=ApiResponse)
async def create_slot(
    slot: SlotCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new time slot (Admin only)"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = "INSERT INTO slot_table (slot_name, day, time_from, till_time) VALUES (%s, %s, %s, %s)"
    result = db.execute_insert(query, (slot.slot_name, slot.day, slot.time_from, slot.till_time))
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create slot")
    
    return ApiResponse(success=True, message="Slot created successfully")

@router.delete("/{slot_id}", response_model=ApiResponse)
async def delete_slot(
    slot_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a time slot (Admin only)"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = "DELETE FROM slot_table WHERE slot_id = %s"
    success = db.execute_update(query, (slot_id,))
    
    if not success:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    return ApiResponse(success=True, message="Slot deleted successfully")