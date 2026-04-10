# backend/routes/timetable_routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel
from services.timetable_service import timetable_service
from auth import get_current_user

router = APIRouter(prefix="/api/timetable", tags=["Timetable"])

class GenerateRequest(BaseModel):
    semester: Optional[int] = None
    department: Optional[str] = None
    priority: str = "lab"

class ConflictResolution(BaseModel):
    resolution: str

@router.post("/generate")
async def generate_timetable(request: GenerateRequest, current_user: dict = Depends(get_current_user)):
    """Generate a new timetable"""
    try:
        result = timetable_service.generate_timetable(
            semester=request.semester,
            department=request.department,
            priority=request.priority
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/view")
async def get_timetable(
    group_id: Optional[int] = Query(None),
    teacher_id: Optional[int] = Query(None),
    room_id: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get timetable with filters"""
    try:
        result = timetable_service.get_timetable(
            group_id=group_id,
            teacher_id=teacher_id,
            room_id=room_id,
            semester=semester
        )
        return {"timetable": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teacher/{teacher_id}")
async def get_teacher_schedule(
    teacher_id: int, 
    semester: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get schedule for a specific teacher"""
    try:
        result = timetable_service.get_teacher_schedule(teacher_id, semester)
        return {"teacher_id": teacher_id, "schedule": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/group/{group_id}")
async def get_group_schedule(
    group_id: int,
    semester: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get schedule for a specific student group"""
    try:
        result = timetable_service.get_group_schedule(group_id, semester)
        return {"group_id": group_id, "schedule": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conflicts")
async def get_conflicts(
    teacher_id: Optional[int] = None,
    group_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get scheduling conflicts"""
    try:
        result = timetable_service.check_conflicts(teacher_id=teacher_id, group_id=group_id)
        return {"conflicts": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    resolution: ConflictResolution,
    current_user: dict = Depends(get_current_user)
):
    """Resolve a scheduling conflict"""
    try:
        success = timetable_service.resolve_conflict(conflict_id, resolution.resolution)
        if not success:
            raise HTTPException(status_code=404, detail="Conflict not found")
        return {"success": True, "message": "Conflict resolved"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_timetable_stats(current_user: dict = Depends(get_current_user)):
    """Get timetable statistics"""
    try:
        timetable = timetable_service.get_timetable()
        return {
            "total_entries": len(timetable),
            "unique_groups": len(set(e['group_id'] for e in timetable)),
            "unique_teachers": len(set(e['teacher_id'] for e in timetable)),
            "unique_rooms": len(set(e['room_id'] for e in timetable))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))