# backend_auth.py - Complete backend with authentication
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
import hashlib
import jwt
import uvicorn
from datetime import datetime, timedelta
import os

# ============ CONFIGURATION ============
SECRET_KEY = "sgsits_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

DB_PATH = "sgsits_timetable.db"

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'teacher', 'student')) DEFAULT 'student',
            branch TEXT,
            year INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teachers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            teacher_code TEXT UNIQUE,
            name TEXT,
            department TEXT,
            max_hours_per_day INTEGER DEFAULT 6,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE,
            subject_name TEXT,
            branch TEXT,
            year INTEGER,
            semester INTEGER,
            credits INTEGER DEFAULT 3,
            hours_per_week INTEGER DEFAULT 3
        )
    ''')
    
    # Subject-Teacher mapping (multiple teachers per subject)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject_teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_id INTEGER,
            is_primary BOOLEAN DEFAULT 0,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    ''')
    
    # Sections
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT,
            branch TEXT,
            year INTEGER,
            student_count INTEGER DEFAULT 60
        )
    ''')
    
    # Timetable entries
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER,
            subject_id INTEGER,
            teacher_id INTEGER,
            room_id INTEGER,
            day_of_week INTEGER,
            start_time TEXT,
            end_time TEXT,
            academic_year TEXT
        )
    ''')
    
    # Rooms
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT UNIQUE,
            room_name TEXT,
            capacity INTEGER
        )
    ''')
    
    # Insert default admin if not exists
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@sgsits.com', admin_hash, 'System Administrator', 'admin'))
    
    # Insert sample rooms
    rooms = [('R101', 'Room 101', 60), ('R102', 'Room 102', 60), ('LAB1', 'Computer Lab', 40)]
    for code, name, cap in rooms:
        cursor.execute('INSERT OR IGNORE INTO rooms (room_code, room_name, capacity) VALUES (?,?,?)', (code, name, cap))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

init_db()

# ============ FASTAPI APP ============
app = FastAPI(title="SGSITS Timetable Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ============ HELPER FUNCTIONS ============
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int, username: str, role: str, full_name: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "full_name": full_name,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    def role_checker(payload: dict = Depends(verify_token)):
        if payload.get("role") != required_role and payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail=f"Access denied. {required_role} role required")
        return payload
    return role_checker

# ============ AUTH ENDPOINTS ============
class LoginData(BaseModel):
    username: str
    password: str

class SignupData(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "student"
    branch: Optional[str] = None
    year: Optional[int] = None

@app.post("/api/auth/login")
async def login(data: LoginData):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (data.username, data.username))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if hash_password(data.password) != user['password_hash']:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'], user['username'], user['role'], user['full_name'])
    
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "full_name": user['full_name'],
            "role": user['role'],
            "branch": user['branch'],
            "year": user['year']
        }
    }

@app.post("/api/auth/signup")
async def signup(data: SignupData):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (data.username, data.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    hashed_pw = hash_password(data.password)
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, full_name, role, branch, year, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', (data.username, data.email, hashed_pw, data.full_name, data.role, data.branch, data.year))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    token = create_token(user_id, data.username, data.role, data.full_name)
    
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_id,
            "username": data.username,
            "full_name": data.full_name,
            "role": data.role,
            "branch": data.branch,
            "year": data.year
        }
    }

@app.get("/api/auth/me")
async def get_current_user(payload: dict = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, role, branch, year FROM users WHERE id = ?", (payload['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

# ============ ADMIN ONLY ENDPOINTS ============
@app.post("/api/admin/teachers")
async def add_teacher(data: dict, payload: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create user account for teacher
    user_hash = hash_password(data.get('password', 'teacher123'))
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES (?, ?, ?, ?, 'teacher')
    ''', (data['username'], data['email'], user_hash, data['name']))
    user_id = cursor.lastrowid
    
    # Create teacher record
    teacher_code = data['name'][:3].upper() + str(user_id)
    cursor.execute('''
        INSERT INTO teachers (user_id, teacher_code, name, department, max_hours_per_day)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, teacher_code, data['name'], data['department'], data.get('max_hours', 6)))
    
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Teacher {data['name']} added"}

@app.get("/api/admin/teachers")
async def get_all_teachers(payload: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers")
    teachers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"teachers": teachers}

@app.post("/api/admin/subjects")
async def add_subject(data: dict, payload: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subjects (subject_code, subject_name, branch, year, semester, credits, hours_per_week)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['subject_code'], data['subject_name'], data['branch'], data['year'], 
          data.get('semester', 1), data.get('credits', 3), data.get('hours_per_week', 3)))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Subject {data['subject_name']} added"}

@app.get("/api/admin/subjects")
async def get_all_subjects(payload: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects")
    subjects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"subjects": subjects}

@app.post("/api/admin/assign-subject")
async def assign_subject_to_teacher(data: dict, payload: dict = Depends(require_role("admin"))):
    """Assign multiple teachers to a subject"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for teacher_id in data['teacher_ids']:
        cursor.execute('''
            INSERT OR REPLACE INTO subject_teachers (subject_id, teacher_id, is_primary)
            VALUES (?, ?, ?)
        ''', (data['subject_id'], teacher_id, teacher_id == data.get('primary_teacher_id')))
    
    conn.commit()
    conn.close()
    return {"success": True, "message": "Subject assigned to teachers"}

@app.post("/api/admin/sections")
async def create_section(data: dict, payload: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sections (section_name, branch, year, student_count)
        VALUES (?, ?, ?, ?)
    ''', (data['section_name'], data['branch'], data['year'], data.get('student_count', 60)))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Section {data['section_name']} created"}

@app.post("/api/admin/generate-timetable")
async def generate_timetable(data: dict, payload: dict = Depends(require_role("admin"))):
    """Generate timetable for a section"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing
    cursor.execute("DELETE FROM timetable_entries WHERE section_id IN (SELECT id FROM sections WHERE section_name = ? AND branch = ? AND year = ?)",
                  (data['section'], data['branch'], data['year']))
    
    # Get subjects for this branch/year
    cursor.execute("SELECT id FROM subjects WHERE branch = ? AND year = ?", (data['branch'], data['year']))
    subjects = cursor.fetchall()
    
    # Get rooms
    cursor.execute("SELECT id FROM rooms")
    rooms = [row[0] for row in cursor.fetchall()]
    
    # Get section ID
    cursor.execute("SELECT id FROM sections WHERE section_name = ? AND branch = ? AND year = ?", 
                  (data['section'], data['branch'], data['year']))
    section = cursor.fetchone()
    
    if not section:
        conn.close()
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Simple scheduling
    time_slots = [(0, '09:00', '10:00'), (0, '10:00', '11:00'), (0, '11:00', '12:00'),
                  (1, '09:00', '10:00'), (1, '10:00', '11:00'), (1, '11:00', '12:00'),
                  (2, '09:00', '10:00'), (2, '10:00', '11:00'), (2, '11:00', '12:00')]
    
    for i, subject in enumerate(subjects):
        if i < len(time_slots):
            day, start, end = time_slots[i]
            room_id = rooms[i % len(rooms)]
            cursor.execute('''
                INSERT INTO timetable_entries (section_id, subject_id, teacher_id, room_id, day_of_week, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (section[0], subject[0], 1, room_id, day, start, end))
    
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Timetable generated for {data['branch']} Year {data['year']} Section {data['section']}"}

# ============ TEACHER ENDPOINTS ============
@app.get("/api/teacher/subjects")
async def get_teacher_subjects(payload: dict = Depends(verify_token)):
    """Get subjects assigned to this teacher"""
    if payload['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.* FROM subjects s
        JOIN subject_teachers st ON s.id = st.subject_id
        JOIN teachers t ON st.teacher_id = t.id
        JOIN users u ON t.user_id = u.id
        WHERE u.id = ?
    ''', (payload['user_id'],))
    
    subjects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"subjects": subjects}

@app.get("/api/teacher/timetable")
async def get_teacher_timetable(payload: dict = Depends(verify_token)):
    """Get timetable for this teacher"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT te.*, s.subject_name, sec.section_name, r.room_name
        FROM timetable_entries te
        JOIN subjects s ON te.subject_id = s.id
        JOIN sections sec ON te.section_id = sec.id
        JOIN rooms r ON te.room_id = r.id
        WHERE te.teacher_id = (SELECT id FROM teachers WHERE user_id = ?)
    ''', (payload['user_id'],))
    
    timetable = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"timetable": timetable}

# ============ STUDENT ENDPOINTS ============
@app.get("/api/student/timetable")
async def get_student_timetable(branch: str, year: int, section: str, payload: dict = Depends(verify_token)):
    """Get timetable for a student based on branch/year/section"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT te.*, s.subject_name, t.name as teacher_name, r.room_name, ts.start_time, ts.end_time
        FROM timetable_entries te
        JOIN subjects s ON te.subject_id = s.id
        JOIN teachers t ON te.teacher_id = t.id
        JOIN rooms r ON te.room_id = r.id
        JOIN sections sec ON te.section_id = sec.id
        WHERE sec.section_name = ? AND sec.branch = ? AND sec.year = ?
    ''', (section, branch, year))
    
    timetable = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Format as matrix
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '14:00-15:00', '15:00-16:00']
    
    matrix = {day: {slot: '—' for slot in time_slots} for day in days}
    for entry in timetable:
        day_name = days[entry['day_of_week']]
        time_key = f"{entry['start_time']}-{entry['end_time']}"
        if time_key in matrix[day_name]:
            matrix[day_name][time_key] = f"{entry['subject_name']}<br>({entry['teacher_name']})"
    
    return {
        "branch": branch,
        "year": year,
        "section": section,
        "days": days,
        "time_slots": time_slots,
        "timetable": matrix
    }

@app.get("/api/public/branches")
async def get_branches():
    return {"branches": ["CSE", "IT", "ECE", "EE", "ME", "CE", "IPE", "BM"]}

@app.get("/api/public/years")
async def get_years():
    return {"years": [1, 2, 3, 4]}

# ============ RUN SERVER ============
if __name__ == "__main__":
    print("="*60)
    print("🚀 SGSITS Timetable Generator API")
    print("="*60)
    print("📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("\n🔐 Default Admin:")
    print("   Username: admin")
    print("   Password: admin123")
    print("="*60)
    uvicorn.run(app, host="127.0.0.1", port=8000)