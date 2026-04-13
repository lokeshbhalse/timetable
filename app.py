# app.py - Simple FastAPI server for timetable generator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional
import uvicorn

DB_PATH = "timetable.db"

app = FastAPI(title="Timetable Generator API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH,timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

# ============ HEALTH CHECK ============
@app.get("/")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Timetable Generator API is running",
        "database": "SQLite",
        "timestamp": str(datetime.now())
    }

# ============ AUTH ENDPOINTS ============
@app.post("/api/auth/login")
async def login(request: dict):
    """User login"""
    username = request.get('username')
    password = request.get('password')
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, password_hash, full_name, role 
        FROM users WHERE username = ? OR email = ?
    """, (username, username))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if hash_password(password) != user['password_hash']:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "name": user['full_name'],
            "role": user['role']
        }
    }

@app.post("/api/auth/signup")
async def signup(request: dict):
    """User registration"""
    username = request.get('username')
    email = request.get('email')
    password = request.get('password')
    full_name = request.get('full_name')
    role = request.get('role', 'student')
    
    if not all([username, email, password, full_name]):
        raise HTTPException(status_code=400, detail="All fields are required")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create user
    hashed_pw = hash_password(password)
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, role, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (username, email, hashed_pw, full_name, role))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "Account created successfully",
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "name": full_name,
            "role": role
        }
    }

# ============ TEACHER ENDPOINTS ============
@app.get("/api/teachers")
async def get_teachers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, teacher_code, name, email, department, designation FROM teachers WHERE is_active = 1")
    teachers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"teachers": teachers}

# ============ GROUP ENDPOINTS ============
@app.get("/api/groups")
async def get_groups():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, group_code, group_name, semester, department, student_count FROM student_groups WHERE is_active = 1")
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"groups": groups}

# ============ ROOM ENDPOINTS ============
@app.get("/api/rooms")
async def get_rooms():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, room_code, room_name, capacity, room_type FROM rooms WHERE is_active = 1")
    rooms = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"rooms": rooms}

# ============ COURSE ENDPOINTS ============
@app.get("/api/courses")
async def get_courses():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, course_code, course_name, credits, hours_per_week, department, semester FROM courses")
    courses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"courses": courses}

@app.get("/api/course-assignments")
async def get_course_assignments():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ca.*, c.course_name, t.name as teacher_name, sg.group_name
        FROM course_assignments ca
        JOIN courses c ON ca.course_id = c.id
        JOIN teachers t ON ca.teacher_id = t.id
        JOIN student_groups sg ON ca.group_id = sg.id
    """)
    assignments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"assignments": assignments}

# ============ TIME SLOT ENDPOINTS ============
@app.get("/api/time-slots")
async def get_time_slots(day: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    if day is not None:
        cursor.execute("SELECT * FROM time_slots WHERE day_of_week = ? AND is_break = 0 ORDER BY start_time", (day,))
    else:
        cursor.execute("SELECT * FROM time_slots WHERE is_break = 0 ORDER BY day_of_week, start_time")
    slots = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"time_slots": slots}

# ============ TIMETABLE GENERATION ============
@app.post("/api/timetable/generate")
async def generate_timetable():
    """Generate a simple timetable"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear existing timetable
    cursor.execute("DELETE FROM timetable_entries")
    
    # Get assignments
    cursor.execute("SELECT * FROM course_assignments")
    assignments = cursor.fetchall()
    
    # Get time slots
    cursor.execute("SELECT id FROM time_slots WHERE is_break = 0 ORDER BY day_of_week, start_time")
    slots = [row['id'] for row in cursor.fetchall()]
    
    # Get rooms
    cursor.execute("SELECT id FROM rooms WHERE is_active = 1")
    rooms = [row['id'] for row in cursor.fetchall()]
    
    # Simple assignment
    for i, assignment in enumerate(assignments):
        if i < len(slots) and i < len(rooms):
            cursor.execute("""
                INSERT INTO timetable_entries (teacher_id, group_id, room_id, slot_id, course_id, semester)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                assignment['teacher_id'],
                assignment['group_id'],
                rooms[i % len(rooms)],
                slots[i % len(slots)],
                assignment['course_id'],
                assignment['semester']
            ))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"Generated {len(assignments)} timetable entries"}

@app.get("/api/timetable/view")
async def view_timetable():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            te.*,
            ts.day_name, ts.start_time, ts.end_time,
            t.name as teacher_name,
            sg.group_name,
            r.room_name,
            c.course_name
        FROM timetable_entries te
        JOIN time_slots ts ON te.slot_id = ts.id
        JOIN teachers t ON te.teacher_id = t.id
        JOIN student_groups sg ON te.group_id = sg.id
        JOIN rooms r ON te.room_id = r.id
        JOIN courses c ON te.course_id = c.id
        ORDER BY sg.group_name, ts.day_of_week, ts.start_time
    """)
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"timetable": entries, "count": len(entries)}

# ============ STATISTICS ============
@app.get("/api/stats")
async def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    cursor.execute("SELECT COUNT(*) as count FROM users")
    stats['users'] = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM teachers")
    stats['teachers'] = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM student_groups")
    stats['groups'] = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM courses")
    stats['courses'] = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM timetable_entries")
    stats['timetable_entries'] = cursor.fetchone()['count']
    
    conn.close()
    return stats

if __name__ == "__main__":
    print("=" * 60)
    print("🎓 Timetable Generator API Server")
    print("=" * 60)
    print(f"📍 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print("\n📋 Default Login Credentials:")
    print("   Admin:    username='admin', password='admin123'")
    print("   Teacher:  username='teacher1', password='123456'")
    print("   Student:  username='student1', password='123456'")
    print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)