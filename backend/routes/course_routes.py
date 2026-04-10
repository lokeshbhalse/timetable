# backend/routes/course_routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from backend.models import CourseCreate, CourseUpdate, CourseResponse, ApiResponse
from backend.database import db
from backend.auth import security, decode_token

router = APIRouter(prefix="/api/courses", tags=["Courses"])

@router.get("/", response_model=List[CourseResponse])
async def get_all_courses(
    semester: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all courses with optional filters"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    query = """
        SELECT course_name, no_of_student as no_of_students, semester, department, 
               lab, preference, preffered_room, preffered_slot, division, lab_room
        FROM course WHERE 1=1
    """
    params = []
    
    if semester:
        query += " AND semester = %s"
        params.append(semester)
    
    if department:
        query += " AND department LIKE %s"
        params.append(f"%{department}%")
    
    results = db.execute_query(query, tuple(params))
    
    if not results:
        return []
    
    # Add id to each result
    for i, result in enumerate(results):
        result['id'] = i + 1
    
    return results

@router.get("/{course_id}")
async def get_course(
    course_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get single course by ID"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Since course table doesn't have an ID column, we'll use LIMIT
    query = """
        SELECT course_name, no_of_student as no_of_students, semester, department, 
               lab, preference, preffered_room, preffered_slot, division, lab_room
        FROM course LIMIT 1 OFFSET %s
    """
    results = db.execute_query(query, (course_id - 1,))
    
    if not results:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return results[0]

@router.post("/", response_model=ApiResponse)
async def create_course(
    course: CourseCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new course"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = """
        INSERT INTO course (course_name, no_of_student, semester, department, lab, 
                           preference, preffered_room, preffered_slot, division, lab_room)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (
        course.course_name, course.no_of_students, course.semester,
        course.department, course.lab, course.preference,
        course.preferred_room, course.preferred_slot,
        course.division, course.lab_room
    )
    
    result = db.execute_insert(query, params)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create course")
    
    return ApiResponse(success=True, message="Course created successfully")

@router.put("/{course_name}", response_model=ApiResponse)
async def update_course(
    course_name: str,
    course: CourseUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update an existing course"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = """
        UPDATE course SET no_of_student = %s, semester = %s, department = %s,
        lab = %s, preference = %s, preffered_room = %s, preffered_slot = %s,
        division = %s, lab_room = %s
        WHERE course_name = %s
    """
    
    params = (
        course.no_of_students, course.semester, course.department,
        course.lab, course.preference, course.preferred_room,
        course.preferred_slot, course.division, course.lab_room,
        course_name
    )
    
    success = db.execute_update(query, params)
    
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return ApiResponse(success=True, message="Course updated successfully")

@router.delete("/{course_name}", response_model=ApiResponse)
async def delete_course(
    course_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a course"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = "DELETE FROM course WHERE course_name = %s"
    success = db.execute_update(query, (course_name,))
    
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return ApiResponse(success=True, message="Course deleted successfully")