# timetable_api.py - Complete backend with dynamic timetable generation
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import sqlite3
import hashlib
from datetime import datetime
import json
import uvicorn
import os

app = FastAPI(title="SGSITS Timetable Generator")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "sgsits_timetable.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Branches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_code TEXT UNIQUE,
            branch_name TEXT,
            short_name TEXT
        )
    ''')
    
    # Years/Semesters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS academic_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            semester INTEGER,
            branch_id INTEGER
        )
    ''')
    
    # Sections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT,
            branch_id INTEGER,
            year_id INTEGER,
            student_count INTEGER DEFAULT 60
        )
    ''')
    
    # Teachers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_code TEXT UNIQUE,
            name TEXT,
            department TEXT,
            email TEXT,
            max_hours_per_day INTEGER DEFAULT 6
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE,
            subject_name TEXT,
            branch_id INTEGER,
            year INTEGER,
            semester INTEGER,
            credits INTEGER,
            is_lab BOOLEAN DEFAULT 0,
            hours_per_week INTEGER DEFAULT 3
        )
    ''')
    
    # Subject-Teacher assignment
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject_teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_id INTEGER,
            section_id INTEGER,
            academic_year TEXT
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
            capacity INTEGER,
            room_type TEXT
        )
    ''')
    
    # Time slots
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_name TEXT,
            day_of_week INTEGER,
            day_name TEXT,
            start_time TEXT,
            end_time TEXT
        )
    ''')
    
    # Insert default branches
    branches = [
        ('CSE', 'Computer Science & Engineering', 'CS'),
        ('IT', 'Information Technology', 'IT'),
        ('ECE', 'Electronics & Communication', 'EC'),
        ('EE', 'Electrical Engineering', 'EE'),
        ('ME', 'Mechanical Engineering', 'ME'),
        ('CE', 'Civil Engineering', 'CE'),
        ('IPE', 'Industrial & Production Engineering', 'IP'),
        ('BM', 'Biomedical Engineering', 'BM'),
    ]
    
    for code, name, short in branches:
        cursor.execute('INSERT OR IGNORE INTO branches (branch_code, branch_name, short_name) VALUES (?,?,?)', (code, name, short))
    
    # Insert default rooms
    rooms = [
        ('R101', 'Room 101', 60, 'Lecture'),
        ('R102', 'Room 102', 60, 'Lecture'),
        ('R103', 'Room 103', 60, 'Lecture'),
        ('R201', 'Room 201', 80, 'Lecture'),
        ('R202', 'Room 202', 80, 'Lecture'),
        ('LAB1', 'Computer Lab 1', 40, 'Lab'),
        ('LAB2', 'Computer Lab 2', 40, 'Lab'),
        ('LAB3', 'Electronics Lab', 40, 'Lab'),
    ]
    
    for code, name, cap, rtype in rooms:
        cursor.execute('INSERT OR IGNORE INTO rooms (room_code, room_name, capacity, room_type) VALUES (?,?,?,?)', (code, name, cap, rtype))
    
    # Insert time slots (Monday to Saturday, 9 AM to 5 PM)
    days = [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday')]
    times = [
        ('S1', '09:00', '10:00'), ('S2', '10:00', '11:00'), ('S3', '11:00', '12:00'),
        ('S4', '12:00', '13:00'), ('S5', '14:00', '15:00'), ('S6', '15:00', '16:00'),
        ('S7', '16:00', '17:00')
    ]
    
    for day_idx, day_name in days:
        for slot_name, start, end in times:
            cursor.execute('''
                INSERT OR IGNORE INTO time_slots (slot_name, day_of_week, day_name, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (f"{day_name[:3]}-{slot_name}", day_idx, day_name, start, end))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

# Initialize database
init_db()

# ============ PYDANTIC MODELS ============
class TeacherData(BaseModel):
    name: str
    department: str
    email: str = ""
    max_hours: int = 6

class SubjectData(BaseModel):
    subject_code: str
    subject_name: str
    branch_code: str
    year: int
    semester: int
    credits: int = 3
    is_lab: bool = False
    hours_per_week: int = 3

class SubjectTeacherAssign(BaseModel):
    subject_code: str
    teacher_name: str
    section_name: str
    branch_code: str
    year: int

class TimetableGenerateRequest(BaseModel):
    branch_code: str
    year: int
    section: str
    semester: int

# ============ API ENDPOINTS ============

@app.get("/")
@app.get("/dashboard")
async def get_dashboard():
    return HTMLResponse(content=open("templates/dashboard.html", "r", encoding="utf-8").read())

@app.get("/api/branches")
async def get_branches():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM branches")
    branches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"branches": branches}

@app.get("/api/years/{branch_code}")
async def get_years(branch_code: str):
    return {"years": [1, 2, 3, 4]}

@app.post("/api/teachers/add")
async def add_teacher(teacher: TeacherData):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    teacher_code = teacher.name[:3].upper() + str(hash(teacher.name))[:4]
    try:
        cursor.execute('''
            INSERT INTO teachers (teacher_code, name, department, email, max_hours_per_day)
            VALUES (?, ?, ?, ?, ?)
        ''', (teacher_code, teacher.name, teacher.department, teacher.email, teacher.max_hours))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Teacher {teacher.name} added successfully"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/teachers")
async def get_teachers(department: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if department:
        cursor.execute("SELECT * FROM teachers WHERE department = ?", (department,))
    else:
        cursor.execute("SELECT * FROM teachers")
    teachers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"teachers": teachers}

@app.post("/api/subjects/add")
async def add_subject(subject: SubjectData):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get branch ID
    cursor.execute("SELECT id FROM branches WHERE branch_code = ?", (subject.branch_code,))
    branch = cursor.fetchone()
    if not branch:
        conn.close()
        raise HTTPException(status_code=404, detail="Branch not found")
    
    try:
        cursor.execute('''
            INSERT INTO subjects (subject_code, subject_name, branch_id, year, semester, credits, is_lab, hours_per_week)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (subject.subject_code, subject.subject_name, branch[0], subject.year, subject.semester, 
              subject.credits, subject.is_lab, subject.hours_per_week))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Subject {subject.subject_name} added successfully"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/subjects/{branch_code}/{year}")
async def get_subjects(branch_code: str, year: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, b.branch_name 
        FROM subjects s
        JOIN branches b ON s.branch_id = b.id
        WHERE b.branch_code = ? AND s.year = ?
    ''', (branch_code, year))
    subjects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"subjects": subjects}

@app.post("/api/assign-subject")
async def assign_subject_to_teacher(assignment: SubjectTeacherAssign):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get IDs
    cursor.execute("SELECT id FROM subjects WHERE subject_code = ?", (assignment.subject_code,))
    subject = cursor.fetchone()
    cursor.execute("SELECT id FROM teachers WHERE name = ?", (assignment.teacher_name,))
    teacher = cursor.fetchone()
    cursor.execute("SELECT id FROM sections WHERE section_name = ?", (assignment.section_name,))
    section = cursor.fetchone()
    
    if not subject or not teacher or not section:
        conn.close()
        raise HTTPException(status_code=404, detail="Subject, teacher, or section not found")
    
    cursor.execute('''
        INSERT OR REPLACE INTO subject_teachers (subject_id, teacher_id, section_id, academic_year)
        VALUES (?, ?, ?, ?)
    ''', (subject[0], teacher[0], section[0], "2024-2025"))
    
    conn.commit()
    conn.close()
    return {"success": True, "message": "Subject assigned successfully"}

@app.post("/api/timetable/generate")
async def generate_timetable(request: TimetableGenerateRequest):
    """Generate automatic timetable for a section"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing timetable for this section
    cursor.execute("DELETE FROM timetable_entries WHERE section_id = (SELECT id FROM sections WHERE section_name = ?)", (request.section,))
    
    # Get section ID
    cursor.execute("SELECT id FROM sections WHERE section_name = ?", (request.section,))
    section = cursor.fetchone()
    if not section:
        # Create section if doesn't exist
        cursor.execute("SELECT id FROM branches WHERE branch_code = ?", (request.branch_code,))
        branch = cursor.fetchone()
        cursor.execute('''
            INSERT INTO sections (section_name, branch_id, year_id)
            VALUES (?, ?, ?)
        ''', (request.section, branch[0], request.year))
        section_id = cursor.lastrowid
    else:
        section_id = section[0]
    
    # Get subjects for this branch and year
    cursor.execute('''
        SELECT s.*, st.teacher_id 
        FROM subjects s
        JOIN subject_teachers st ON s.id = st.subject_id
        WHERE s.branch_id = (SELECT id FROM branches WHERE branch_code = ?) 
        AND s.year = ?
        AND st.section_id = ?
    ''', (request.branch_code, request.year, section_id))
    
    subjects = cursor.fetchall()
    
    # Get time slots
    cursor.execute("SELECT * FROM time_slots ORDER BY day_of_week, start_time")
    slots = cursor.fetchall()
    
    # Get rooms
    cursor.execute("SELECT id FROM rooms")
    rooms = [row[0] for row in cursor.fetchall()]
    
    # Simple scheduling algorithm
    timetable = []
    for idx, subject in enumerate(subjects):
        if idx < len(slots):
            slot = slots[idx]
            room_id = rooms[idx % len(rooms)]
            timetable.append({
                'section_id': section_id,
                'subject_id': subject[0],
                'teacher_id': subject[7],  # teacher_id from subject_teachers
                'room_id': room_id,
                'day_of_week': slot[2],
                'start_time': slot[4],
                'end_time': slot[5],
                'academic_year': "2024-2025"
            })
            
            cursor.execute('''
                INSERT INTO timetable_entries 
                (section_id, subject_id, teacher_id, room_id, day_of_week, start_time, end_time, academic_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (section_id, subject[0], subject[7], room_id, slot[2], slot[4], slot[5], "2024-2025"))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"Timetable generated with {len(timetable)} entries"}

@app.get("/api/timetable/view/{branch_code}/{year}/{section}")
async def view_timetable(branch_code: str, year: int, section: str):
    """View generated timetable in table format"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT te.*, 
               s.subject_code, s.subject_name,
               t.name as teacher_name,
               r.room_name,
               ts.day_name, ts.start_time, ts.end_time
        FROM timetable_entries te
        JOIN subjects s ON te.subject_id = s.id
        JOIN teachers t ON te.teacher_id = t.id
        JOIN rooms r ON te.room_id = r.id
        JOIN time_slots ts ON te.day_of_week = ts.day_of_week AND te.start_time = ts.start_time
        WHERE te.section_id = (SELECT id FROM sections WHERE section_name = ?)
        ORDER BY ts.day_of_week, ts.start_time
    ''', (section,))
    
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Organize by day and time
    timetable_matrix = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', 
                  '14:00-15:00', '15:00-16:00', '16:00-17:00']
    
    for day in days:
        timetable_matrix[day] = {time: '—' for time in time_slots}
    
    for entry in entries:
        time_key = f"{entry['start_time']}-{entry['end_time']}"
        if time_key in timetable_matrix[entry['day_name']]:
            timetable_matrix[entry['day_name']][time_key] = f"{entry['subject_code']}<br>({entry['teacher_name']})"
    
    return {
        "branch": branch_code,
        "year": year,
        "section": section,
        "days": days,
        "time_slots": time_slots,
        "timetable": timetable_matrix
    }

@app.post("/api/sections/create")
async def create_section(branch_code: str, year: int, section_name: str, student_count: int = 60):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM branches WHERE branch_code = ?", (branch_code,))
    branch = cursor.fetchone()
    if not branch:
        conn.close()
        raise HTTPException(status_code=404, detail="Branch not found")
    
    cursor.execute('''
        INSERT OR IGNORE INTO sections (section_name, branch_id, year_id, student_count)
        VALUES (?, ?, ?, ?)
    ''', (section_name, branch[0], year, student_count))
    
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Section {section_name} created"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)