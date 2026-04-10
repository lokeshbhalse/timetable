# backend_api.py - Complete Working Version
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
import jwt
import uvicorn
import os
import random

app = FastAPI(title="SGSITS Timetable API")

# ============ CORS FIX - Allow all origins for development ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
SECRET_KEY = "your-secret-key-2024"
ALGORITHM = "HS256"

# Database setup
DB_PATH = "sgsits_timetable.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Drop existing tables to recreate with correct schema
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS teachers")
    cursor.execute("DROP TABLE IF EXISTS subjects")
    cursor.execute("DROP TABLE IF EXISTS timetable")
    cursor.execute("DROP TABLE IF EXISTS rooms")
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teachers table
    cursor.execute('''
        CREATE TABLE teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Rooms table (create BEFORE subjects)
    cursor.execute('''
        CREATE TABLE rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT UNIQUE,
            room_name TEXT,
            capacity INTEGER,
            room_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT,
            branch TEXT,
            year INTEGER,
            teacher_id INTEGER,
            teacher2_id INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            FOREIGN KEY (teacher2_id) REFERENCES teachers(id)
        )
    ''')
    
    # Timetable entries
    cursor.execute('''
        CREATE TABLE timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch TEXT,
            year INTEGER,
            section TEXT,
            subject_id INTEGER,
            teacher_id INTEGER,
            day TEXT,
            time_slot TEXT,
            room_id INTEGER,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    ''')
    
    print("✅ Tables created")
    
    # Insert default admin
    admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role) VALUES (?,?,?,?,?)",
                   ("admin", "admin@sgsits.edu", admin_pw, "Administrator", "admin"))
    
    # Insert sample teachers
    teachers = [
        ("Prof. Rahul Sharma", "rahul@sgsits.edu", "CSE"),
        ("Prof. Neha Verma", "neha@sgsits.edu", "CSE"),
        ("Prof. Amit Tiwari", "amit@sgsits.edu", "EE"),
        ("Prof. Priya Patel", "priya@sgsits.edu", "ME"),
        ("Prof. Sanjay Gupta", "sanjay@sgsits.edu", "CSE"),
        ("Prof. Vikram Singh", "vikram@sgsits.edu", "ECE"),
        ("Prof. Anjali Mehta", "anjali@sgsits.edu", "CE"),
        ("Prof. Rajesh Kumar", "rajesh@sgsits.edu", "IT"),
    ]
    for t in teachers:
        cursor.execute("INSERT OR IGNORE INTO teachers (name, email, department) VALUES (?,?,?)", t)
    
    # Insert sample rooms
    rooms = [
        ("R101", "Room 101", 60, "lecture"),
        ("R102", "Room 102", 50, "lecture"),
        ("R103", "Room 103", 50, "lecture"),
        ("R104", "Room 104", 55, "lecture"),
        ("R201", "Room 201", 80, "lecture"),
        ("R202", "Room 202", 70, "lecture"),
        ("R203", "Room 203", 65, "lecture"),
        ("LAB1", "Computer Lab 1", 40, "lab"),
        ("LAB2", "Computer Lab 2", 40, "lab"),
        ("LAB3", "Electronics Lab", 35, "lab"),
        ("LAB4", "Physics Lab", 40, "lab"),
        ("LAB5", "Chemistry Lab", 40, "lab"),
    ]
    for code, name, cap, rtype in rooms:
        cursor.execute("INSERT OR IGNORE INTO rooms (room_code, room_name, capacity, room_type) VALUES (?,?,?,?)",
                      (code, name, cap, rtype))
    
    # Get teacher IDs for subject assignment
    cursor.execute("SELECT id FROM teachers")
    teacher_ids = [row['id'] for row in cursor.fetchall()]
    
    if not teacher_ids:
        teacher_ids = [1, 2, 3, 4, 5]
    
    # Insert sample subjects for all branches and years
    branches = ['CSE', 'EE', 'ME', 'ECE', 'CE', 'IT']
    years = [1, 2, 3, 4]
    
    subject_counter = 1
    for branch in branches:
        for year in years:
            # Create 5-6 subjects per branch per year
            subjects_data = [
                (f"{branch}{year}01", f"Subject {year}01", branch, year, teacher_ids[0] if teacher_ids else 1, teacher_ids[1] if len(teacher_ids) > 1 else None),
                (f"{branch}{year}02", f"Subject {year}02", branch, year, teacher_ids[0] if teacher_ids else 1, None),
                (f"{branch}{year}03", f"Subject {year}03", branch, year, teacher_ids[1] if len(teacher_ids) > 1 else teacher_ids[0], None),
                (f"{branch}{year}04", f"Subject {year}04", branch, year, teacher_ids[2] if len(teacher_ids) > 2 else teacher_ids[0], None),
                (f"{branch}{year}05", f"Subject {year}05", branch, year, teacher_ids[0] if teacher_ids else 1, teacher_ids[1] if len(teacher_ids) > 1 else None),
                (f"{branch}{year}06", f"Subject {year}06 Lab", branch, year, teacher_ids[2] if len(teacher_ids) > 2 else teacher_ids[0], None),
            ]
            for s in subjects_data:
                cursor.execute("INSERT OR IGNORE INTO subjects (code, name, branch, year, teacher_id, teacher2_id) VALUES (?,?,?,?,?,?)", s)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with correct schema")
    print("✅ Sample teachers, subjects, and rooms created")

# Initialize database
init_db()

# ============ AUTH FUNCTIONS ============
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ============ AUTH ENDPOINTS ============
class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "student"

class TeacherData(BaseModel):
    name: str
    email: str
    department: str

class SubjectData(BaseModel):
    code: str
    name: str
    branch: str
    year: int
    teacher_id: int
    teacher2_id: Optional[int] = None

class TimetableGenerateRequest(BaseModel):
    branch: str
    year: int
    section: str

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    print(f"Login attempt for username: {request.username}")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (request.username, request.username))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        print(f"User not found: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user['password_hash'] != hash_password(request.password):
        print(f"Password incorrect for: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'], user['username'], user['role'])
    print(f"Login successful for: {request.username}, role: {user['role']}")
    
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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (request.username, request.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")
    
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?,?,?,?,?)",
        (request.username, request.email, hash_password(request.password), request.full_name, request.role)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    
    token = create_token(user_id, request.username, request.role)
    return {"success": True, "token": token, "user": {"id": user_id, "username": request.username, "role": request.role}}

# ============ TEACHER ENDPOINTS ============
@app.post("/api/admin/teachers")
async def add_teacher(teacher: TeacherData, _=Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO teachers (name, email, department) VALUES (?,?,?)",
                   (teacher.name, teacher.email, teacher.department))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Teacher {teacher.name} added"}

@app.get("/api/teachers")
async def get_teachers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers")
    teachers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"teachers": teachers}

# ============ SUBJECT ENDPOINTS ============
@app.post("/api/admin/subjects")
async def add_subject(subject: SubjectData, _=Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subjects (code, name, branch, year, teacher_id, teacher2_id) VALUES (?,?,?,?,?,?)",
        (subject.code, subject.name, subject.branch, subject.year, subject.teacher_id, subject.teacher2_id)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Subject {subject.name} added"}

@app.get("/api/subjects/{branch}/{year}")
async def get_subjects(branch: str, year: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, t1.name as teacher1_name, t2.name as teacher2_name 
        FROM subjects s
        LEFT JOIN teachers t1 ON s.teacher_id = t1.id
        LEFT JOIN teachers t2 ON s.teacher2_id = t2.id
        WHERE s.branch = ? AND s.year = ?
    ''', (branch, year))
    subjects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"subjects": subjects}

# ============ TIMETABLE ENDPOINTS ============
@app.post("/api/timetable/generate")
async def generate_timetable(request: TimetableGenerateRequest, current_user=Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear existing timetable for this section
    cursor.execute("DELETE FROM timetable WHERE branch = ? AND year = ? AND section = ?",
                   (request.branch, request.year, request.section))
    
    # Get subjects for this branch and year
    cursor.execute("SELECT * FROM subjects WHERE branch = ? AND year = ?", (request.branch, request.year))
    subjects = cursor.fetchall()
    
    if not subjects:
        conn.close()
        return {"success": False, "message": "No subjects found for this branch and year"}
    
    # Time slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', 
                  '14:00-15:00', '15:00-16:00', '16:00-17:00']
    
    # Get rooms
    cursor.execute("SELECT id FROM rooms")
    rooms = cursor.fetchall()
    room_ids = [room['id'] for room in rooms] if rooms else [1, 2, 3, 4, 5]
    
    entries_count = 0
    for i, subject in enumerate(subjects):
        day_index = (entries_count // len(time_slots)) % len(days)
        time_index = entries_count % len(time_slots)
        
        day = days[day_index]
        time = time_slots[time_index]
        room_id = room_ids[i % len(room_ids)]
        
        teacher_id = subject['teacher_id'] if subject['teacher_id'] else subject['teacher2_id']
        if not teacher_id:
            cursor.execute("SELECT id FROM teachers LIMIT 1")
            first_teacher = cursor.fetchone()
            teacher_id = first_teacher['id'] if first_teacher else 1
        
        cursor.execute('''
            INSERT INTO timetable (branch, year, section, subject_id, teacher_id, day, time_slot, room_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (request.branch, request.year, request.section, subject['id'], teacher_id, day, time, room_id))
        
        entries_count += 1
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"Timetable generated with {entries_count} entries"}

@app.get("/api/timetable/view/{branch}/{year}/{section}")
async def view_timetable(branch: str, year: int, section: str, current_user=Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, s.name as subject_name, s.code as subject_code,
               tc.name as teacher_name, r.room_code
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN teachers tc ON t.teacher_id = tc.id
        JOIN rooms r ON t.room_id = r.id
        WHERE t.branch = ? AND t.year = ? AND t.section = ?
        ORDER BY 
            CASE t.day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
            END,
            CASE t.time_slot
                WHEN '09:00-10:00' THEN 1
                WHEN '10:00-11:00' THEN 2
                WHEN '11:00-12:00' THEN 3
                WHEN '12:00-13:00' THEN 4
                WHEN '14:00-15:00' THEN 5
                WHEN '15:00-16:00' THEN 6
                WHEN '16:00-17:00' THEN 7
            END
    ''', (branch, year, section))
    
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', 
                  '14:00-15:00', '15:00-16:00', '16:00-17:00']
    
    matrix = {day: {slot: '—' for slot in time_slots} for day in days}
    
    for entry in entries:
        matrix[entry['day']][entry['time_slot']] = f"{entry['subject_code']}<br>({entry['teacher_name']})"
    
    for day in days:
        matrix[day]['12:00-13:00'] = '🍽️ LUNCH BREAK'
    
    return {
        "branch": branch,
        "year": year,
        "section": section,
        "days": days,
        "time_slots": time_slots,
        "entries": entries,
        "timetable": matrix
    }

# ============ ROOMS ENDPOINTS ============
@app.get("/api/rooms")
async def get_rooms():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, room_code, room_name, capacity, room_type FROM rooms")
    rooms = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"rooms": rooms}

# ============ BRANCHES ============
@app.get("/api/branches")
async def get_branches():
    return {"branches": [
        {"code": "CSE", "name": "Computer Science & Engineering"},
        {"code": "EE", "name": "Electrical Engineering"},
        {"code": "ME", "name": "Mechanical Engineering"},
        {"code": "ECE", "name": "Electronics & Communication"},
        {"code": "CE", "name": "Civil Engineering"},
        {"code": "IT", "name": "Information Technology"}
    ]}

@app.get("/")
async def root():
    return {"message": "SGSITS Timetable API is running", "status": "healthy"}

if __name__ == "__main__":
    print("="*50)
    print("🚀 SGSITS Timetable API Server")
    print("="*50)
    print("📍 API: http://localhost:8000")
    print("📍 Docs: http://localhost:8000/docs")
    print("="*50)
    print("🔐 Default Admin Login:")
    print("   Username: admin")
    print("   Password: admin123")
    print("="*50)
    print("✅ CORS enabled - All origins allowed")
    print("✅ Database ready with sample data")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)