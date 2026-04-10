# backend/routes/faculty_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models import FacultyCreate, FacultyResponse, ApiResponse
from backend.database import db
from backend.auth import security, decode_token, get_password_hash

router = APIRouter(prefix="/api/faculty", tags=["Faculty"])

@router.get("/", response_model=List[FacultyResponse])
async def get_all_faculty(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all faculty members"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    query = "SELECT fac_id, name, email, department FROM facultyreg"
    results = db.execute_query(query)
    
    return results or []

@router.post("/", response_model=ApiResponse)
async def create_faculty(
    faculty: FacultyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new faculty member (Admin only)"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Insert into facultyreg
    faculty_query = """
        INSERT INTO facultyreg (name, email, department) 
        VALUES (%s, %s, %s)
    """
    faculty_id = db.execute_insert(faculty_query, (faculty.name, faculty.email, faculty.department))
    
    if not faculty_id:
        raise HTTPException(status_code=500, detail="Failed to create faculty")
    
    # Create user account
    hashed_password = get_password_hash(faculty.password)
    user_query = "INSERT INTO user_master (UserName, Password) VALUES (%s, %s)"
    db.execute_insert(user_query, (faculty.email, hashed_password))
    
    return ApiResponse(success=True, message="Faculty created successfully")