# main.py - Complete Main Entry Point with Admin Routes
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import from backend
from backend.database import get_db, init_db
from db_queries import db_queries
from backend.legacy.Bipartite_Matching_Assignment import create_timetable_scheduler
from backend.services.timetable_service import timetable_service
from backend.routes import admin_routes

# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Timetable Generator API...")
    init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(
    title="Timetable Generator API",
    description="Complete Timetable Management System with Teacher Collision Prevention",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ INCLUDE ADMIN ROUTES ============
app.include_router(admin_routes.router)

# ============ HEALTH CHECK ============
@app.get("/")
async def root():
    return {
        "message": "Timetable Generator API",
        "version": "2.0.0",
        "status": "running",
        "database": "SQLite",
        "endpoints": {
            "health": "/api/health",
            "teachers": "/api/teachers",
            "groups": "/api/groups",
            "rooms": "/api/rooms",
            "courses": "/api/courses",
            "timetable": "/api/timetable/generate",
            "admin": "/api/admin/users"
        }
    }

@app.get("/api/health")
async def health_check():
    import datetime
    return {
        "status": "healthy", 
        "database": "connected",
        "timestamp": str(datetime.datetime.now())
    }

# ============ TEACHER ENDPOINTS ============
@app.get("/api/teachers")
async def get_all_teachers():
    """Get all teachers"""
    return {"teachers": db_queries.get_all_teachers()}

@app.get("/api/teachers/{teacher_id}/schedule")
async def get_teacher_schedule(teacher_id: int, week: int = 1):
    """Get teacher's schedule"""
    schedule = db_queries.get_teacher_weekly_schedule(teacher_id, week)
    return {"teacher_id": teacher_id, "schedule": schedule}

@app.get("/api/teachers/{teacher_id}/available-slots")
async def get_teacher_available_slots(teacher_id: int, day: int = None):
    """Get available time slots for a teacher"""
    slots = db_queries.get_available_slots_for_teacher(teacher_id, day)
    return {"teacher_id": teacher_id, "available_slots": slots}

# ============ GROUP ENDPOINTS ============
@app.get("/api/groups")
async def get_all_groups(semester: int = None, department: str = None):
    """Get all student groups"""
    groups = db_queries.get_all_groups(semester, department)
    return {"groups": groups}

@app.get("/api/groups/{group_id}/timetable")
async def get_group_timetable(group_id: int, week: int = 1):
    """Get timetable for a specific group"""
    timetable = timetable_service.get_group_schedule(group_id)
    return {"group_id": group_id, "timetable": timetable}

# ============ ROOM ENDPOINTS ============
@app.get("/api/rooms")
async def get_all_rooms(room_type: str = None):
    """Get all rooms"""
    rooms = db_queries.get_all_rooms(room_type)
    return {"rooms": rooms}

@app.get("/api/rooms/available")
async def get_available_rooms(slot_id: int, capacity: int = 0, is_lab: bool = False):
    """Get available rooms for a specific time slot"""
    rooms = db_queries.get_available_rooms_for_slot(slot_id, capacity, is_lab)
    return {"slot_id": slot_id, "available_rooms": rooms}

# ============ COURSE ENDPOINTS ============
@app.get("/api/courses")
async def get_all_courses(department: str = None, semester: int = None):
    """Get all courses"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM courses WHERE 1=1"
        params = []
        if department:
            query += " AND department = ?"
            params.append(department)
        if semester:
            query += " AND semester = ?"
            params.append(semester)
        cursor.execute(query, params)
        courses = [dict(row) for row in cursor.fetchall()]
    
    return {"courses": courses}

@app.get("/api/course-assignments")
async def get_course_assignments(teacher_id: int = None, group_id: int = None, semester: int = None):
    """Get course assignments"""
    assignments = db_queries.get_course_assignments(teacher_id, group_id, semester)
    return {"assignments": assignments}

# ============ TIMETABLE GENERATION ============
@app.post("/api/timetable/generate")
async def generate_timetable(request: dict):
    """Generate a new timetable using the scheduling algorithm"""
    try:
        branch = request.get("branch")
        semester = request.get("semester")
        priority = request.get("priority", "lab")
        department = branch or request.get("department")

        result = timetable_service.generate_timetable(
            semester=semester,
            department=department,
            priority=priority
        )

        return {
            "success": True,
            "message": "Timetable generated successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timetable/view")
async def view_timetable(
    group_id: int = None,
    teacher_id: int = None,
    room_id: int = None,
    branch: str = None,
    year: int = None,
    section: str = None,
    semester: int = None
):
    """View generated timetable"""
    resolved_group_id = group_id

    if branch or section or semester or year:
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT id FROM student_groups WHERE 1=1"
            params = []
            if branch:
                query += " AND department = ?"
                params.append(branch)
            if section:
                query += " AND group_code = ?"
                params.append(section)
            if semester:
                query += " AND semester = ?"
                params.append(semester)
            elif year:
                # Map year to semester range if year is provided
                if year == 1:
                    query += " AND semester IN (1, 2)"
                elif year == 2:
                    query += " AND semester IN (3, 4)"
                elif year == 3:
                    query += " AND semester IN (5, 6)"
                elif year == 4:
                    query += " AND semester IN (7, 8)"
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            if row:
                resolved_group_id = row['id']

    result = timetable_service.get_timetable(resolved_group_id, teacher_id, room_id)
    return {"timetable": result, "count": len(result)}

@app.get("/api/branches")
async def get_branches():
    """Get distinct branch list for timetable selection"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department AS branch FROM student_groups WHERE department IS NOT NULL ORDER BY department")
        branches = [row['branch'] for row in cursor.fetchall()]
    return {"branches": branches}

# ============ CONFLICT MANAGEMENT ============
@app.get("/api/conflicts")
async def get_conflicts(resolved: bool = False):
    """Get scheduling conflicts"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conflict_log WHERE resolved = ?", (1 if resolved else 0,))
        conflicts = [dict(row) for row in cursor.fetchall()]
    
    return {"conflicts": conflicts, "count": len(conflicts)}

@app.post("/api/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: int):
    """Resolve a conflict"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE conflict_log 
            SET resolved = 1, resolved_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (conflict_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conflict not found")
    
    return {"success": True, "message": "Conflict resolved"}

# ============ STATISTICS ============
@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) as count FROM teachers WHERE is_active = 1")
        stats['teachers'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM student_groups WHERE is_active = 1")
        stats['groups'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM rooms WHERE is_active = 1")
        stats['rooms'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM courses")
        stats['courses'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM timetable_entries WHERE status = 'scheduled'")
        stats['timetable_entries'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM conflict_log WHERE resolved = 0")
        stats['unresolved_conflicts'] = cursor.fetchone()['count']
    
    return stats

# ============ TIME SLOTS ============
@app.get("/api/time-slots")
async def get_time_slots(day: int = None):
    """Get time slots"""
    if day is not None:
        slots = db_queries.get_slots_by_day(day)
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM time_slots WHERE is_active = 1 ORDER BY day_of_week, start_time")
            slots = [dict(row) for row in cursor.fetchall()]
    
    return {"time_slots": slots}

# ============ AUTH ENDPOINTS (for compatibility) ============
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "student"

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login endpoint - uses existing auth service"""
    from backend.auth import authenticate_user, create_token
    import hashlib
    
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (request.username,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if user['password_hash'] != hash_password(request.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_token(user['id'], user['username'], user['role'])
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role']
            }
        }

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    """Signup endpoint"""
    import hashlib
    
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (request.username, request.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Create user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (request.username, request.email, hash_password(request.password), request.full_name, request.role, 1))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        from backend.auth import create_token
        token = create_token(user_id, request.username, request.role)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user_id,
                "username": request.username,
                "email": request.email,
                "full_name": request.full_name,
                "role": request.role
            }
        }

# ============ RUN SERVER ============
if __name__ == "__main__":
    print("=" * 60)
    print("🎓 Timetable Generator API Server")
    print("=" * 60)
    print(f"📍 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🗄️  Database: SQLite (timetable.db)")
    print("=" * 60)
    print("\n📋 Available Endpoints:")
    print("   GET  /api/health - Health check")
    print("   GET  /api/teachers - List all teachers")
    print("   GET  /api/groups - List student groups")
    print("   GET  /api/rooms - List all rooms")
    print("   GET  /api/courses - List all courses")
    print("   POST /api/timetable/generate - Generate timetable")
    print("   GET  /api/timetable/view - View timetable")
    print("   GET  /api/conflicts - View conflicts")
    print("   GET  /api/admin/users - Admin: Get all users")
    print("   POST /api/admin/teachers - Admin: Add teacher")
    print("   POST /api/admin/subjects - Admin: Add subject")
    print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)