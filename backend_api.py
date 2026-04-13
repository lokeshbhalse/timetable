# backend_api.py - Complete SGSITS Timetable API v4.0
# Matches all frontend API calls exactly

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict
from contextlib import asynccontextmanager
import sqlite3
import hashlib
from datetime import datetime, timedelta
import jwt
import uvicorn
import json

# ============================================================
# CONFIG
# ============================================================
DB_PATH = "sgsits_timetable.db"
SECRET_KEY = "your-secret-key-change-this-to-32-chars!!"
ALGORITHM = "HS256"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = [
    "09:00-10:00", "10:00-11:00", "11:00-12:00",
    "12:00-13:00",
    "14:00-15:00", "15:00-16:00", "16:00-17:00"
]
LUNCH_SLOT = "12:00-13:00"

# ============================================================
# MIGRATIONS
# Runs on every startup. Adds any missing columns automatically.
# Rule: whenever you add a column to CREATE TABLE, also add it here.
# ============================================================
MIGRATIONS = [
    # (table, column, sql_definition)
    ("subjects",           "credits",            "INTEGER DEFAULT 3"),
    ("subjects",           "hours_per_week",      "INTEGER DEFAULT 3"),
    ("subjects",           "is_lab",              "BOOLEAN DEFAULT 0"),
    ("subjects",           "teacher_id",          "INTEGER"),
    ("subjects",           "teacher2_id",         "INTEGER"),
    ("subjects",           "semester",            "INTEGER DEFAULT 1"),
    ("subjects",           "branch",              "TEXT"),
    ("subjects",           "year",                "INTEGER DEFAULT 1"),

    ("teachers",           "designation",         "TEXT"),
    ("teachers",           "specialization",      "TEXT"),
    ("teachers",           "max_hours_per_day",   "INTEGER DEFAULT 6"),
    ("teachers",           "max_hours_per_week",  "INTEGER DEFAULT 24"),
    ("teachers",           "is_active",           "BOOLEAN DEFAULT 1"),

    ("rooms",              "building",            "TEXT"),
    ("rooms",              "floor",               "INTEGER"),
    ("rooms",              "has_projector",       "BOOLEAN DEFAULT 0"),
    ("rooms",              "has_whiteboard",      "BOOLEAN DEFAULT 1"),
    ("rooms",              "has_ac",              "BOOLEAN DEFAULT 0"),
    ("rooms",              "has_computers",       "BOOLEAN DEFAULT 0"),
    ("rooms",              "is_lab",              "BOOLEAN DEFAULT 0"),
    ("rooms",              "room_type",           "TEXT DEFAULT 'lecture'"),
    ("rooms",              "is_active",           "BOOLEAN DEFAULT 1"),

    ("courses",            "description",         "TEXT"),
    ("courses",            "theory_hours",        "INTEGER DEFAULT 2"),
    ("courses",            "lab_hours",           "INTEGER DEFAULT 1"),
    ("courses",            "is_lab",              "BOOLEAN DEFAULT 0"),
    ("courses",            "is_elective",         "BOOLEAN DEFAULT 0"),
    ("courses",            "department",          "TEXT"),
    ("courses",            "semester",            "INTEGER"),

    ("course_assignments", "theory_hours",        "INTEGER DEFAULT 2"),
    ("course_assignments", "lab_hours",           "INTEGER DEFAULT 1"),
    ("course_assignments", "is_lab",              "BOOLEAN DEFAULT 0"),
    ("course_assignments", "priority",            "INTEGER DEFAULT 1"),
    ("course_assignments", "is_elective",         "BOOLEAN DEFAULT 0"),
    ("course_assignments", "academic_year",       "TEXT DEFAULT '2024-2025'"),
    ("course_assignments", "hours_per_week",      "INTEGER DEFAULT 3"),

    ("student_groups",     "academic_year",       "TEXT"),
    ("student_groups",     "student_count",       "INTEGER DEFAULT 0"),
    ("student_groups",     "is_active",           "BOOLEAN DEFAULT 1"),

    ("timetable_entries",  "academic_year",       "TEXT DEFAULT '2024-2025'"),
    ("timetable_entries",  "status",              "TEXT DEFAULT 'scheduled'"),
    ("timetable_entries",  "week_number",         "INTEGER DEFAULT 1"),

    ("saved_timetables",   "generated_by",        "INTEGER"),
    ("saved_timetables",   "is_active",           "BOOLEAN DEFAULT 1"),

    ("users",              "is_active",           "BOOLEAN DEFAULT 1"),

    ("conflict_log",       "severity",            "TEXT DEFAULT 'warning'"),
    ("conflict_log",       "resolved",            "BOOLEAN DEFAULT 0"),
    ("conflict_log",       "resolved_at",         "TIMESTAMP"),
    ("conflict_log",       "teacher_id",          "INTEGER"),
    ("conflict_log",       "group_id",            "INTEGER"),
    ("conflict_log",       "room_id",             "INTEGER"),
    ("conflict_log",       "slot_id",             "INTEGER"),

    ("holidays",           "is_optional",         "BOOLEAN DEFAULT 0"),
    ("holidays",           "description",         "TEXT"),

    ("time_slots",         "duration",            "INTEGER DEFAULT 60"),
    ("time_slots",         "slot_type",           "TEXT DEFAULT 'lecture'"),
    ("time_slots",         "is_break",            "BOOLEAN DEFAULT 0"),
    ("time_slots",         "is_active",           "BOOLEAN DEFAULT 1"),
]


def run_migrations(conn):
    """Check every table for missing columns and ALTER TABLE to add them."""
    cursor = conn.cursor()
    migrated = 0

    for table, column, definition in MIGRATIONS:
        # Skip if table doesn't exist yet (init_db will create it)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            continue

        # Check existing columns
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row["name"] for row in cursor.fetchall()}

        if column not in existing:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                print(f"  ✅ Migration: added {table}.{column}")
                migrated += 1
            except Exception as e:
                print(f"  ⚠️  Migration failed {table}.{column}: {e}")

    conn.commit()
    if migrated:
        print(f"✅ Migrations complete: {migrated} column(s) added")
    else:
        print("✅ Schema up to date, no migrations needed")


# ============================================================
# DATABASE
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT CHECK(role IN ("admin","teacher","student")) DEFAULT "student",
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        designation TEXT,
        specialization TEXT,
        max_hours_per_day INTEGER DEFAULT 6,
        max_hours_per_week INTEGER DEFAULT 24,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT UNIQUE NOT NULL,
        room_name TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        room_type TEXT DEFAULT "lecture",
        building TEXT,
        floor INTEGER,
        has_projector BOOLEAN DEFAULT 0,
        has_whiteboard BOOLEAN DEFAULT 1,
        has_ac BOOLEAN DEFAULT 0,
        has_computers BOOLEAN DEFAULT 0,
        is_lab BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        branch TEXT NOT NULL,
        year INTEGER NOT NULL,
        semester INTEGER DEFAULT 1,
        credits INTEGER DEFAULT 3,
        hours_per_week INTEGER DEFAULT 3,
        is_lab BOOLEAN DEFAULT 0,
        teacher_id INTEGER,
        teacher2_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id),
        FOREIGN KEY (teacher2_id) REFERENCES teachers(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        description TEXT,
        credits INTEGER DEFAULT 3,
        hours_per_week INTEGER DEFAULT 3,
        theory_hours INTEGER DEFAULT 2,
        lab_hours INTEGER DEFAULT 1,
        is_lab BOOLEAN DEFAULT 0,
        is_elective BOOLEAN DEFAULT 0,
        department TEXT,
        semester INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS student_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_code TEXT UNIQUE NOT NULL,
        group_name TEXT NOT NULL,
        semester INTEGER NOT NULL,
        department TEXT NOT NULL,
        academic_year TEXT,
        student_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS course_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        semester INTEGER NOT NULL,
        academic_year TEXT DEFAULT "2024-2025",
        hours_per_week INTEGER DEFAULT 3,
        theory_hours INTEGER DEFAULT 2,
        lab_hours INTEGER DEFAULT 1,
        is_lab BOOLEAN DEFAULT 0,
        priority INTEGER DEFAULT 1,
        is_elective BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(id),
        FOREIGN KEY (teacher_id) REFERENCES teachers(id),
        FOREIGN KEY (group_id) REFERENCES student_groups(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS time_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_code TEXT NOT NULL,
        day_of_week INTEGER NOT NULL,
        day_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration INTEGER DEFAULT 60,
        slot_type TEXT DEFAULT "lecture",
        is_break BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS timetable_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        slot_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        semester INTEGER NOT NULL,
        academic_year TEXT DEFAULT "2024-2025",
        status TEXT DEFAULT "scheduled",
        week_number INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id),
        FOREIGN KEY (group_id) REFERENCES student_groups(id),
        FOREIGN KEY (room_id) REFERENCES rooms(id),
        FOREIGN KEY (slot_id) REFERENCES time_slots(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS saved_timetables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch TEXT NOT NULL,
        year INTEGER NOT NULL,
        section TEXT NOT NULL,
        semester INTEGER NOT NULL,
        timetable_data TEXT NOT NULL,
        generated_by INTEGER,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS conflict_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conflict_type TEXT,
        severity TEXT DEFAULT "warning",
        teacher_id INTEGER,
        group_id INTEGER,
        room_id INTEGER,
        slot_id INTEGER,
        conflict_description TEXT,
        resolved BOOLEAN DEFAULT 0,
        resolved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        holiday_name TEXT NOT NULL,
        holiday_date DATE UNIQUE NOT NULL,
        is_optional BOOLEAN DEFAULT 0,
        description TEXT
    )''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_teachers_dept ON teachers(department)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subjects_branch_year ON subjects(branch, year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ca_teacher ON course_assignments(teacher_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ca_group ON course_assignments(group_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tt_group ON timetable_entries(group_id, slot_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tt_teacher ON timetable_entries(teacher_id, slot_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_slots_day ON time_slots(day_of_week)')

    # ✅ Run migrations BEFORE inserting sample data
    conn.commit()
    run_migrations(conn)

    _insert_sample_data(cursor)
    conn.commit()
    conn.close()
    print("✅ Database initialized")


def _insert_sample_data(cursor):
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        return

    print("📝 Inserting sample data...")

    admin_pw   = hashlib.sha256("admin123".encode()).hexdigest()
    teacher_pw = hashlib.sha256("teacher123".encode()).hexdigest()
    student_pw = hashlib.sha256("student123".encode()).hexdigest()

    for u, e, p, fn, r in [
        ("admin",    "admin@sgsits.edu",    admin_pw,   "Administrator",      "admin"),
        ("teacher1", "teacher1@sgsits.edu", teacher_pw, "Prof. Rahul Sharma", "teacher"),
        ("teacher2", "teacher2@sgsits.edu", teacher_pw, "Prof. Neha Verma",   "teacher"),
        ("teacher",  "teacher@sgsits.edu",  teacher_pw, "Demo Teacher",       "teacher"),
        ("student1", "student1@sgsits.edu", student_pw, "John Student",       "student"),
        ("student",  "student@sgsits.edu",  student_pw, "Demo Student",       "student"),
    ]:
        cursor.execute(
            "INSERT OR IGNORE INTO users (username,email,password_hash,full_name,role,is_active) VALUES (?,?,?,?,?,1)",
            (u, e, p, fn, r))

    for n, e, d, dg, sp, md, mw in [
        ("Prof. Rahul Sharma", "rahul@sgsits.edu",  "CSE",  "Professor",           "Data Structures",   6, 24),
        ("Prof. Neha Verma",   "neha@sgsits.edu",   "CSE",  "Associate Professor", "Algorithms",        6, 24),
        ("Prof. Amit Tiwari",  "amit@sgsits.edu",   "EE",   "Professor",           "Circuit Theory",    5, 20),
        ("Prof. Priya Patel",  "priya@sgsits.edu",  "ME",   "Assistant Professor", "Thermodynamics",    5, 20),
        ("Prof. Sanjay Gupta", "sanjay@sgsits.edu", "CSE",  "Professor",           "Operating Systems", 6, 24),
        ("Prof. Meena Singh",  "meena@sgsits.edu",  "Math", "Associate Professor", "Applied Math",      6, 24),
        ("Prof. Ravi Kumar",   "ravi@sgsits.edu",   "PHY",  "Professor",           "Quantum Physics",   5, 20),
    ]:
        cursor.execute(
            "INSERT OR IGNORE INTO teachers (name,email,department,designation,specialization,max_hours_per_day,max_hours_per_week,is_active) VALUES (?,?,?,?,?,?,?,1)",
            (n, e, d, dg, sp, md, mw))

    for code, name, cap, rtype, building, floor, proj, board, ac, comp, is_lab in [
        ("R101", "Room 101",       60,  "lecture",    "Main Building", 1, 1, 1, 1, 0, 0),
        ("R102", "Room 102",       50,  "lecture",    "Main Building", 1, 0, 1, 0, 0, 0),
        ("R201", "Room 201",       80,  "lecture",    "Main Building", 2, 1, 1, 1, 0, 0),
        ("LAB1", "Computer Lab 1", 40,  "lab",        "Lab Block",     1, 1, 0, 0, 1, 1),
        ("LAB2", "Computer Lab 2", 40,  "lab",        "Lab Block",     1, 1, 0, 0, 1, 1),
        ("LAB3", "Physics Lab",    40,  "lab",        "Science Block", 1, 1, 0, 0, 0, 1),
        ("AUD1", "Auditorium",     200, "auditorium", "Main Building", 1, 1, 1, 1, 0, 0),
    ]:
        cursor.execute(
            "INSERT OR IGNORE INTO rooms (room_code,room_name,capacity,room_type,building,floor,has_projector,has_whiteboard,has_ac,has_computers,is_lab,is_active) VALUES (?,?,?,?,?,?,?,?,?,?,?,1)",
            (code, name, cap, rtype, building, floor, proj, board, ac, comp, is_lab))

    for code, name, desc, credits, hours, theory, lab, is_lab, dept, sem in [
        ("CS301",   "Data Structures",     "DSA",        4, 4, 3, 1, 0, "CSE",  3),
        ("CS302",   "Algorithms",          "Algorithms", 4, 4, 3, 1, 0, "CSE",  3),
        ("CS303",   "Operating Systems",   "OS",         3, 3, 2, 1, 0, "CSE",  5),
        ("CS101",   "Programming in C",    "Intro",      3, 3, 2, 1, 0, "CSE",  1),
        ("EE201",   "Circuit Theory",      "Circuits",   3, 3, 2, 1, 0, "EE",   2),
        ("ME101",   "Engg Mechanics",      "Mechanics",  3, 3, 2, 1, 0, "ME",   1),
        ("MATH201", "Mathematics II",      "Calculus",   4, 4, 3, 1, 0, "Math", 3),
        ("PHY101",  "Engineering Physics", "Physics",    3, 3, 2, 1, 0, "PHY",  1),
    ]:
        cursor.execute(
            "INSERT OR IGNORE INTO courses (course_code,course_name,description,credits,hours_per_week,theory_hours,lab_hours,is_lab,department,semester) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (code, name, desc, credits, hours, theory, lab, is_lab, dept, sem))

    for code, name, branch, year, sem, credits, hours, is_lab in [
        ("CS301",  "Data Structures",     "CSE", 2, 3, 4, 4, 0),
        ("CS302",  "Algorithms",          "CSE", 2, 3, 4, 4, 0),
        ("CS101",  "Programming in C",    "CSE", 1, 1, 3, 3, 0),
        ("EE201",  "Circuit Theory",      "EE",  1, 2, 3, 3, 0),
        ("ME101",  "Engg Mechanics",      "ME",  1, 1, 3, 3, 0),
    ]:
        cursor.execute(
            "INSERT OR IGNORE INTO subjects (code,name,branch,year,semester,credits,hours_per_week,is_lab) VALUES (?,?,?,?,?,?,?,?)",
            (code, name, branch, year, sem, credits, hours, is_lab))

    for code, name, sem, dept, year, count in [
        ("CSE1A", "CSE Year 1 Sec A", 1, "CSE", "2024-2025", 60),
        ("CSE1B", "CSE Year 1 Sec B", 1, "CSE", "2024-2025", 58),
        ("CSE2A", "CSE Year 2 Sec A", 3, "CSE", "2024-2025", 60),
        ("CSE2B", "CSE Year 2 Sec B", 3, "CSE", "2024-2025", 58),
        ("CSE3A", "CSE Year 3 Sec A", 5, "CSE", "2024-2025", 55),
        ("CSE4A", "CSE Year 4 Sec A", 7, "CSE", "2024-2025", 50),
        ("EE1A",  "EE Year 1 Sec A",  1, "EE",  "2024-2025", 55),
        ("ME1A",  "ME Year 1 Sec A",  1, "ME",  "2024-2025", 58),
    ]:
        cursor.execute(
            "INSERT OR IGNORE INTO student_groups (group_code,group_name,semester,department,academic_year,student_count,is_active) VALUES (?,?,?,?,?,?,1)",
            (code, name, sem, dept, year, count))

    slot_id = 1
    for day_idx, day_name in enumerate(DAYS):
        for code, start, end, stype, is_break in [
            ("S1",    "09:00", "10:00", "lecture", 0),
            ("S2",    "10:00", "11:00", "lecture", 0),
            ("S3",    "11:00", "12:00", "lecture", 0),
            ("LUNCH", "12:00", "13:00", "break",   1),
            ("S4",    "14:00", "15:00", "lecture", 0),
            ("S5",    "15:00", "16:00", "lecture", 0),
            ("S6",    "16:00", "17:00", "lecture", 0),
        ]:
            cursor.execute(
                "INSERT OR IGNORE INTO time_slots (id,slot_code,day_of_week,day_name,start_time,end_time,duration,slot_type,is_break,is_active) VALUES (?,?,?,?,?,?,60,?,?,1)",
                (slot_id, f"{day_name[:3]}{code}", day_idx, day_name, start, end, stype, is_break))
            slot_id += 1

    cursor.execute("SELECT id FROM teachers ORDER BY id")
    tids = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM courses ORDER BY id")
    cids = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM student_groups ORDER BY id")
    gids = [r[0] for r in cursor.fetchall()]

    if tids and cids and gids:
        for cid, tid, gid, sem, hours in [
            (cids[0], tids[0], gids[2], 3, 4),
            (cids[0], tids[0], gids[3], 3, 4),
            (cids[1], tids[1], gids[2], 3, 4),
            (cids[4], tids[2], gids[6], 2, 3),
            (cids[5], tids[3], gids[7], 1, 3),
            (cids[6], tids[5], gids[0], 3, 4),
            (cids[7], tids[6], gids[0], 1, 3),
        ]:
            cursor.execute(
                "INSERT OR IGNORE INTO course_assignments (course_id,teacher_id,group_id,semester,hours_per_week) VALUES (?,?,?,?,?)",
                (cid, tid, gid, sem, hours))

    for name, date, opt in [
        ("Republic Day",     "2024-01-26", 0),
        ("Independence Day", "2024-08-15", 0),
        ("Gandhi Jayanti",   "2024-10-02", 0),
        ("Christmas",        "2024-12-25", 0),
    ]:
        cursor.execute(
            "INSERT OR IGNORE INTO holidays (holiday_name,holiday_date,is_optional) VALUES (?,?,?)",
            (name, date, opt))

    print("✅ Sample data inserted!")


# ============================================================
# APP
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting SGSITS Timetable API v4.0...")
    init_db()
    yield
    print("👋 Shutting down...")

app = FastAPI(title="SGSITS Timetable API", version="4.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBearer()


# ============================================================
# AUTH HELPERS
# ============================================================
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

def create_token(user_id: int, username: str, role: str) -> str:
    return jwt.encode(
        {"user_id": user_id, "username": username, "role": role,
         "exp": datetime.now() + timedelta(days=7)},
        SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ============================================================
# MODELS
# ============================================================
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
    designation: Optional[str] = None
    specialization: Optional[str] = None
    max_hours_per_day: Optional[int] = 6
    max_hours_per_week: Optional[int] = 24

class RoomData(BaseModel):
    room_code: str
    room_name: str
    capacity: int
    room_type: str = "lecture"
    building: Optional[str] = None
    floor: Optional[int] = None
    has_projector: Optional[bool] = False
    has_ac: Optional[bool] = False
    has_computers: Optional[bool] = False
    is_lab: Optional[bool] = False

class SubjectData(BaseModel):
    code: str
    name: str
    branch: str
    year: int
    semester: int = 1
    credits: Optional[int] = 3
    hours_per_week: Optional[int] = 3
    is_lab: Optional[bool] = False
    teacher_id: int
    teacher2_id: Optional[int] = None

class CourseData(BaseModel):
    course_code: str
    course_name: str
    description: Optional[str] = None
    credits: int = 3
    hours_per_week: int = 3
    theory_hours: int = 2
    lab_hours: int = 1
    is_lab: bool = False
    department: Optional[str] = None
    semester: Optional[int] = None

class CourseAssignmentData(BaseModel):
    course_id: int
    teacher_id: int
    group_id: int
    semester: int
    hours_per_week: int = 3
    theory_hours: int = 2
    lab_hours: int = 1
    is_lab: bool = False

class TimetableGenerateRequest(BaseModel):
    branch: str
    year: int
    section: str
    semester: int = 1

class ConflictResolveRequest(BaseModel):
    resolution_note: Optional[str] = None


# ============================================================
# MATRIX HELPERS
# ============================================================
def _empty_matrix() -> Dict:
    m = {day: {slot: "—" for slot in TIME_SLOTS} for day in DAYS}
    for day in DAYS:
        m[day][LUNCH_SLOT] = "🍽️ LUNCH BREAK"
    return m

def _build_timetable_response(branch, year, section, semester, entries_list, saved_entries=None):
    matrix = _empty_matrix()
    source = saved_entries if saved_entries is not None else entries_list
    for entry in source:
        if saved_entries is not None:
            day      = entry.get("day")
            slot_key = entry.get("time_slot")
            cell     = f"{entry.get('subject_code','')}<br>({entry.get('teacher_name','')})"
        else:
            day      = entry.get("day_name")
            slot_key = f"{entry.get('start_time')}-{entry.get('end_time')}"
            cell     = f"{entry.get('course_code','')}<br>({entry.get('teacher_name','')})"
        if day and slot_key and day in matrix and slot_key in matrix[day] and slot_key != LUNCH_SLOT:
            matrix[day][slot_key] = cell
    return {"branch": branch, "year": year, "semester": semester, "section": section,
            "days": DAYS, "time_slots": TIME_SLOTS, "timetable": matrix}


# ============================================================
# ROOT / HEALTH
# ============================================================
@app.get("/")
async def root():
    return {"message": "SGSITS Timetable API v4.0", "status": "running", "docs": "/docs"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": str(datetime.now())}


# ============================================================
# AUTH
# ============================================================
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE (username=? OR email=?) AND is_active=1",
            (request.username, request.username))
        user = cursor.fetchone()
        if not user or user["password_hash"] != hash_password(request.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token(user["id"], user["username"], user["role"])
        return {"success": True, "token": token,
                "user": {"id": user["id"], "username": user["username"],
                         "email": user["email"], "full_name": user["full_name"], "role": user["role"]}}
    finally:
        conn.close()

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? OR email=?", (request.username, request.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        cursor.execute(
            "INSERT INTO users (username,email,password_hash,full_name,role,is_active) VALUES (?,?,?,?,?,1)",
            (request.username, request.email, hash_password(request.password), request.full_name, request.role))
        conn.commit()
        user_id = cursor.lastrowid
        token = create_token(user_id, request.username, request.role)
        return {"success": True, "token": token,
                "user": {"id": user_id, "username": request.username,
                         "email": request.email, "full_name": request.full_name, "role": request.role}}
    finally:
        conn.close()


# ============================================================
# ADMIN — USERS
# ============================================================
@app.get("/api/admin/users")
async def get_all_users(_=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id,username,email,full_name,role,is_active,created_at FROM users ORDER BY created_at DESC")
        return {"users": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.put("/api/admin/users/{user_id}/status")
async def update_user_status(user_id: int, request: dict, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active=? WHERE id=?", (request.get("is_active", 1), user_id))
        conn.commit()
        return {"success": True, "message": "User status updated"}
    finally:
        conn.close()

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
        if user and user["role"] == "admin":
            raise HTTPException(status_code=403, detail="Cannot delete admin user")
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        return {"success": True, "message": "User deleted"}
    finally:
        conn.close()


# ============================================================
# TEACHERS
# ============================================================
@app.get("/api/admin/teachers")
async def get_teachers_admin(_=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teachers WHERE is_active=1 ORDER BY name")
        return {"teachers": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.post("/api/admin/teachers")
async def add_teacher(teacher: TeacherData, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM teachers WHERE email=?", (teacher.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Teacher with email {teacher.email} already exists")
        cursor.execute(
            "INSERT INTO teachers (name,email,department,designation,specialization,max_hours_per_day,max_hours_per_week,is_active) VALUES (?,?,?,?,?,?,?,1)",
            (teacher.name, teacher.email, teacher.department, teacher.designation,
             teacher.specialization, teacher.max_hours_per_day, teacher.max_hours_per_week))
        conn.commit()
        return {"success": True, "message": f"Teacher {teacher.name} added", "id": cursor.lastrowid}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/api/admin/teachers/{teacher_id}")
async def update_teacher(teacher_id: int, teacher: TeacherData, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE teachers SET name=?,email=?,department=?,designation=?,specialization=?,max_hours_per_day=?,max_hours_per_week=? WHERE id=?",
            (teacher.name, teacher.email, teacher.department, teacher.designation,
             teacher.specialization, teacher.max_hours_per_day, teacher.max_hours_per_week, teacher_id))
        conn.commit()
        return {"success": True, "message": "Teacher updated"}
    finally:
        conn.close()

@app.delete("/api/admin/teachers/{teacher_id}")
async def delete_teacher(teacher_id: int, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE teachers SET is_active=0 WHERE id=?", (teacher_id,))
        conn.commit()
        return {"success": True, "message": "Teacher deactivated"}
    finally:
        conn.close()

@app.get("/api/teachers")
async def get_teachers_public(department: Optional[str] = None):
    conn = get_db()
    try:
        cursor = conn.cursor()
        if department:
            cursor.execute("SELECT * FROM teachers WHERE department=? AND is_active=1", (department,))
        else:
            cursor.execute("SELECT * FROM teachers WHERE is_active=1 ORDER BY name")
        return {"teachers": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.get("/api/teachers/{teacher_id}/schedule")
async def get_teacher_schedule_by_id(teacher_id: int, _=Depends(get_current_user)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT te.*, ts.day_name, ts.start_time, ts.end_time,
                   c.course_code, c.course_name,
                   sg.group_name, sg.group_code,
                   r.room_code, r.room_name
            FROM timetable_entries te
            JOIN time_slots ts ON te.slot_id=ts.id
            JOIN courses c ON te.course_id=c.id
            JOIN student_groups sg ON te.group_id=sg.id
            JOIN rooms r ON te.room_id=r.id
            WHERE te.teacher_id=? AND te.status="scheduled"
            ORDER BY ts.day_of_week, ts.start_time
        ''', (teacher_id,))
        entries = [dict(r) for r in cursor.fetchall()]
        matrix = _empty_matrix()
        for e in entries:
            day = e["day_name"]
            sk  = f"{e['start_time']}-{e['end_time']}"
            if day in matrix and sk in matrix[day] and sk != LUNCH_SLOT:
                matrix[day][sk] = f"{e['course_code']}<br>({e['group_code']})<br>{e['room_code']}"
        return {"teacher_id": teacher_id, "schedule": entries, "matrix": matrix, "total_classes": len(entries)}
    finally:
        conn.close()

@app.get("/api/teacher/schedule")
async def get_my_schedule(current_user=Depends(get_current_user)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    conn = get_db()
    try:
        cursor = conn.cursor()
        username = current_user.get("username")
        cursor.execute("SELECT id FROM teachers WHERE email LIKE ? AND is_active=1", (f"%{username}%",))
        teacher = cursor.fetchone()
        if not teacher:
            return {"schedule": [], "matrix": _empty_matrix(), "total_classes": 0}
        cursor.execute('''
            SELECT te.*, ts.day_name, ts.start_time, ts.end_time,
                   c.course_code, c.course_name, sg.group_name, sg.group_code, r.room_code
            FROM timetable_entries te
            JOIN time_slots ts ON te.slot_id=ts.id
            JOIN courses c ON te.course_id=c.id
            JOIN student_groups sg ON te.group_id=sg.id
            JOIN rooms r ON te.room_id=r.id
            WHERE te.teacher_id=? AND te.status="scheduled"
            ORDER BY ts.day_of_week, ts.start_time
        ''', (teacher["id"],))
        entries = [dict(r) for r in cursor.fetchall()]
        matrix = _empty_matrix()
        for e in entries:
            day = e["day_name"]
            sk  = f"{e['start_time']}-{e['end_time']}"
            if day in matrix and sk in matrix[day] and sk != LUNCH_SLOT:
                matrix[day][sk] = f"{e['course_code']}<br>({e['group_code']})<br>{e['room_code']}"
        return {"teacher_name": username, "schedule": entries, "matrix": matrix, "total_classes": len(entries)}
    finally:
        conn.close()


# ============================================================
# ROOMS
# ============================================================
@app.get("/api/rooms")
async def get_rooms(room_type: Optional[str] = None):
    conn = get_db()
    try:
        cursor = conn.cursor()
        if room_type:
            cursor.execute("SELECT * FROM rooms WHERE room_type=? AND is_active=1", (room_type,))
        else:
            cursor.execute("SELECT * FROM rooms WHERE is_active=1")
        return {"rooms": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.post("/api/admin/rooms")
async def add_room(room: RoomData, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rooms (room_code,room_name,capacity,room_type,building,floor,has_projector,has_ac,has_computers,is_lab,is_active) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
            (room.room_code, room.room_name, room.capacity, room.room_type, room.building,
             room.floor, room.has_projector, room.has_ac, room.has_computers, room.is_lab))
        conn.commit()
        return {"success": True, "message": f"Room {room.room_code} added", "id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/rooms/available")
async def get_available_rooms(slot_id: int, capacity: int = 0, is_lab: bool = False):
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = '''SELECT r.* FROM rooms r WHERE r.is_active=1 AND r.capacity>=?
                   AND r.id NOT IN (SELECT room_id FROM timetable_entries WHERE slot_id=? AND status="scheduled")'''
        params = [capacity, slot_id]
        if is_lab:
            query += " AND r.is_lab=1"
        cursor.execute(query, params)
        return {"slot_id": slot_id, "available_rooms": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()


# ============================================================
# SUBJECTS
# ============================================================
@app.get("/api/admin/subjects")
async def get_subjects_admin(
    branch: Optional[str] = None,
    year: Optional[int] = None,
    _=Depends(require_admin)
):
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = '''
            SELECT s.*, t1.name as teacher1_name, t2.name as teacher2_name
            FROM subjects s
            LEFT JOIN teachers t1 ON s.teacher_id=t1.id
            LEFT JOIN teachers t2 ON s.teacher2_id=t2.id
            WHERE 1=1
        '''
        params = []
        if branch:
            query += " AND s.branch=?"; params.append(branch)
        if year:
            query += " AND s.year=?"; params.append(year)
        query += " ORDER BY s.name"
        cursor.execute(query, params)
        return {"subjects": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.post("/api/admin/subjects")
async def add_subject(subject: SubjectData, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM subjects WHERE code=?", (subject.code,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Subject code {subject.code} already exists")
        cursor.execute(
            "INSERT INTO subjects (code,name,branch,year,semester,credits,hours_per_week,is_lab,teacher_id,teacher2_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (subject.code, subject.name, subject.branch, subject.year, subject.semester,
             subject.credits, subject.hours_per_week, subject.is_lab,
             subject.teacher_id, subject.teacher2_id))
        subject_id = cursor.lastrowid

        cursor.execute("SELECT id FROM courses WHERE course_code=?", (subject.code,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO courses (course_code,course_name,credits,hours_per_week,is_lab,department,semester) VALUES (?,?,?,?,?,?,?)",
                (subject.code, subject.name, subject.credits, subject.hours_per_week,
                 subject.is_lab, subject.branch, subject.semester))

        conn.commit()
        return {"success": True, "message": f"Subject {subject.name} added", "id": subject_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/admin/subjects/assign")
async def assign_subject(data: dict, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()

        subject_id = data.get("subject_id")
        teacher_id = data.get("teacher_id")
        section    = data.get("section", "A")
        branch     = data.get("branch")
        year       = data.get("year", 1)

        # Validate all required fields up front
        if not subject_id or not teacher_id or not section or not branch:
            raise HTTPException(
                status_code=422,
                detail="Missing required fields: subject_id, teacher_id, section, branch"
            )
        if not isinstance(year, int) or year < 1:
            raise HTTPException(
                status_code=422,
                detail=f"year must be a positive integer, got: {year!r}"
            )

        # Fetch subject and convert to dict IMMEDIATELY before any other cursor use
        cursor.execute("SELECT * FROM subjects WHERE id=?", (subject_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Subject with id={subject_id} not found")
        subject = dict(row)  # ✅ plain dict — safe across all subsequent cursor operations

        # Assign teacher to subject
        cursor.execute("UPDATE subjects SET teacher_id=? WHERE id=?", (teacher_id, subject_id))

        # Create student group if not exists
        group_code = f"{branch}{year}{section}"
        cursor.execute("SELECT id FROM student_groups WHERE group_code=?", (group_code,))
        group_row = cursor.fetchone()
        if not group_row:
            cursor.execute(
                "INSERT INTO student_groups (group_code,group_name,semester,department,academic_year,student_count,is_active) VALUES (?,?,?,?,?,60,1)",
                (group_code, f"{branch} Year {year} Sec {section}",
                 subject["semester"], branch, "2024-2025"))
            group_id = cursor.lastrowid
        else:
            group_id = group_row["id"]

        # Ensure course record exists
        cursor.execute("SELECT id FROM courses WHERE course_code=?", (subject["code"],))
        course_row = cursor.fetchone()
        if not course_row:
            cursor.execute(
                "INSERT INTO courses (course_code,course_name,credits,hours_per_week,is_lab,department,semester) VALUES (?,?,?,?,?,?,?)",
                (subject["code"], subject["name"], subject["credits"],
                 subject["hours_per_week"], subject["is_lab"], branch, subject["semester"]))
            course_id = cursor.lastrowid
        else:
            course_id = course_row["id"]

        # Create course assignment if not exists
        cursor.execute(
            "SELECT id FROM course_assignments WHERE course_id=? AND teacher_id=? AND group_id=?",
            (course_id, teacher_id, group_id))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO course_assignments (course_id,teacher_id,group_id,semester,hours_per_week) VALUES (?,?,?,?,?)",
                (course_id, teacher_id, group_id, subject["semester"], subject["hours_per_week"]))

        conn.commit()
        return {"success": True, "message": f"Subject assigned to section {section} successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/subjects/{branch}/{year}")
async def get_subjects_legacy(branch: str, year: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, t1.name as teacher1_name, t2.name as teacher2_name
            FROM subjects s
            LEFT JOIN teachers t1 ON s.teacher_id=t1.id
            LEFT JOIN teachers t2 ON s.teacher2_id=t2.id
            WHERE s.branch=? AND s.year=?
        ''', (branch, year))
        return {"subjects": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()


# ============================================================
# COURSES
# ============================================================
@app.get("/api/courses")
async def get_courses(department: Optional[str] = None, semester: Optional[int] = None):
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM courses WHERE 1=1"
        params = []
        if department:
            query += " AND department=?"; params.append(department)
        if semester:
            query += " AND semester=?"; params.append(semester)
        cursor.execute(query, params)
        return {"courses": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.post("/api/admin/courses")
async def add_course(course: CourseData, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO courses (course_code,course_name,description,credits,hours_per_week,theory_hours,lab_hours,is_lab,department,semester) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (course.course_code, course.course_name, course.description, course.credits,
             course.hours_per_week, course.theory_hours, course.lab_hours,
             course.is_lab, course.department, course.semester))
        conn.commit()
        return {"success": True, "message": f"Course {course.course_code} added", "id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# STUDENT GROUPS
# ============================================================
@app.get("/api/groups")
async def get_groups(semester: Optional[int] = None, department: Optional[str] = None):
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM student_groups WHERE is_active=1"
        params = []
        if semester:
            query += " AND semester=?"; params.append(semester)
        if department:
            query += " AND department=?"; params.append(department)
        cursor.execute(query, params)
        return {"groups": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.get("/api/groups/{group_id}/timetable")
async def get_group_timetable(group_id: int, _=Depends(get_current_user)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT te.*, ts.day_name, ts.start_time, ts.end_time,
                   c.course_code, c.course_name, t.name as teacher_name, r.room_code
            FROM timetable_entries te
            JOIN time_slots ts ON te.slot_id=ts.id
            JOIN courses c ON te.course_id=c.id
            JOIN teachers t ON te.teacher_id=t.id
            JOIN rooms r ON te.room_id=r.id
            WHERE te.group_id=? AND te.status="scheduled"
            ORDER BY ts.day_of_week, ts.start_time
        ''', (group_id,))
        return {"group_id": group_id, "timetable": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()


# ============================================================
# COURSE ASSIGNMENTS
# ============================================================
@app.get("/api/course-assignments")
async def get_course_assignments(
    teacher_id: Optional[int] = None,
    group_id: Optional[int] = None,
    semester: Optional[int] = None,
    _=Depends(get_current_user)
):
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = '''
            SELECT ca.*, c.course_name, c.course_code,
                   t.name as teacher_name, sg.group_name, sg.group_code
            FROM course_assignments ca
            JOIN courses c ON ca.course_id=c.id
            JOIN teachers t ON ca.teacher_id=t.id
            JOIN student_groups sg ON ca.group_id=sg.id
            WHERE 1=1
        '''
        params = []
        if teacher_id:
            query += " AND ca.teacher_id=?"; params.append(teacher_id)
        if group_id:
            query += " AND ca.group_id=?"; params.append(group_id)
        if semester:
            query += " AND ca.semester=?"; params.append(semester)
        cursor.execute(query, params)
        return {"assignments": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.post("/api/admin/course-assignments")
async def add_course_assignment(data: CourseAssignmentData, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO course_assignments (course_id,teacher_id,group_id,semester,hours_per_week,theory_hours,lab_hours,is_lab) VALUES (?,?,?,?,?,?,?,?)",
            (data.course_id, data.teacher_id, data.group_id, data.semester,
             data.hours_per_week, data.theory_hours, data.lab_hours, data.is_lab))
        conn.commit()
        return {"success": True, "message": "Course assignment created", "id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# TIME SLOTS
# ============================================================
@app.get("/api/time-slots")
async def get_time_slots(day: Optional[int] = None):
    conn = get_db()
    try:
        cursor = conn.cursor()
        if day is not None:
            cursor.execute("SELECT * FROM time_slots WHERE day_of_week=? AND is_active=1 ORDER BY start_time", (day,))
        else:
            cursor.execute("SELECT * FROM time_slots WHERE is_active=1 ORDER BY day_of_week, start_time")
        return {"time_slots": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()


# ============================================================
# BRANCHES
# ============================================================
@app.get("/api/branches")
async def get_branches():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM student_groups WHERE department IS NOT NULL ORDER BY department")
        from_db = [r[0] for r in cursor.fetchall()]
        names = {"CSE":"Computer Science & Engineering","EE":"Electrical Engineering",
                 "ME":"Mechanical Engineering","ECE":"Electronics & Communication",
                 "CE":"Civil Engineering","IT":"Information Technology"}
        branches = [{"code": b, "name": names.get(b, b)} for b in (from_db or list(names.keys()))]
        return {"branches": branches}
    finally:
        conn.close()


# ============================================================
# TIMETABLE GENERATION
# ============================================================
@app.post("/api/timetable/generate")
async def generate_timetable(request: TimetableGenerateRequest, current_user=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        year_label = {1:"FY",2:"SY",3:"TY",4:"Final"}.get(request.year, f"Y{request.year}")
        group_code = f"{request.branch}{request.year}{request.section}"

        cursor.execute("SELECT id FROM student_groups WHERE group_code=?", (group_code,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO student_groups (group_code,group_name,semester,department,academic_year,student_count,is_active) VALUES (?,?,?,?,?,60,1)",
                (group_code, f"{request.branch} {year_label} Sec {request.section}",
                 request.semester, request.branch, "2024-2025"))
            group_id = cursor.lastrowid
        else:
            group_id = row["id"]

        cursor.execute("DELETE FROM timetable_entries WHERE group_id=? AND semester=?", (group_id, request.semester))

        cursor.execute('''
            SELECT ca.*, c.course_code, c.course_name, t.name as teacher_name, t.id as tid
            FROM course_assignments ca
            JOIN courses c ON ca.course_id=c.id
            JOIN teachers t ON ca.teacher_id=t.id
            WHERE ca.group_id=? AND ca.semester=?
            ORDER BY ca.priority DESC
        ''', (group_id, request.semester))
        assignments = cursor.fetchall()

        if not assignments:
            cursor.execute('''
                SELECT ca.*, c.course_code, c.course_name, t.name as teacher_name, t.id as tid
                FROM course_assignments ca
                JOIN courses c ON ca.course_id=c.id
                JOIN teachers t ON ca.teacher_id=t.id
                JOIN student_groups sg ON ca.group_id=sg.id
                WHERE sg.department=? AND ca.semester=?
                ORDER BY ca.priority DESC
            ''', (request.branch, request.semester))
            assignments = cursor.fetchall()

        if not assignments:
            return {"success": False,
                    "message": f"No course assignments found for {request.branch} Semester {request.semester}. Add subjects and assign teachers first."}

        # Get all non-break slots ordered by day then time
        cursor.execute("SELECT * FROM time_slots WHERE is_break=0 AND is_active=1 ORDER BY day_of_week, start_time")
        available_slots = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT id FROM rooms WHERE is_active=1 ORDER BY capacity DESC")
        room_ids = [r["id"] for r in cursor.fetchall()]

        if not room_ids:
            return {"success": False, "message": "No active rooms found. Add rooms first."}

        # Track what's occupied
        teacher_busy: Dict[int, set] = {}   # teacher_id -> set of slot_ids
        room_busy:    Dict[int, set] = {}   # room_id    -> set of slot_ids
        group_busy:   set            = set() # set of slot_ids already assigned for this group

        entries_list = []
        assigned_count = 0
        conflicts = []

        # Convert to plain dicts immediately
        assignments = [dict(a) for a in assignments]

        # Calculate total hours needed
        total_hours_needed = sum(a["hours_per_week"] for a in assignments)
        total_slots_available = len(available_slots)  # 5 days × 6 slots = 30 usable slots

        # Build a schedule slot by slot
        # Strategy: round-robin across assignments, spreading evenly across the week
        # Each subject gets slots spread across different days where possible

        # First pass: track how many slots each assignment still needs
        remaining = {i: a["hours_per_week"] for i, a in enumerate(assignments)}

        # Sort slots to spread across days (interleave days instead of filling one day at a time)
        # Reorder slots: slot 0 of each day, then slot 1 of each day, etc.
        slots_by_position: Dict[int, list] = {}
        for slot in available_slots:
            # group by start_time position within the day
            pos_key = slot["start_time"]
            if pos_key not in slots_by_position:
                slots_by_position[pos_key] = []
            slots_by_position[pos_key].append(slot)

        # Interleaved order: for each time position, go through all days
        interleaved_slots = []
        for pos_key in sorted(slots_by_position.keys()):
            interleaved_slots.extend(slots_by_position[pos_key])

        # Assign slots greedily, cycling through subjects
        slot_index = 0
        max_iterations = total_slots_available * len(assignments) * 2  # safety limit
        iterations = 0

        while slot_index < len(interleaved_slots) and iterations < max_iterations:
            iterations += 1
            slot = interleaved_slots[slot_index]
            slot_id = slot["id"]

            # Skip if group already has something this slot
            if slot_id in group_busy:
                slot_index += 1
                continue

            # Find the next assignment that still needs hours
            # Pick the one with the most remaining hours (greedy fill)
            best_idx = None
            best_remaining = 0
            for i, assignment in enumerate(assignments):
                if remaining[i] <= 0:
                    continue
                tid = assignment["tid"]
                # Check teacher not busy this slot
                if tid in teacher_busy and slot_id in teacher_busy[tid]:
                    conflicts.append({
                        "type": "teacher",
                        "description": f"Teacher {assignment['teacher_name']} busy at slot {slot_id}"
                    })
                    continue
                if remaining[i] > best_remaining:
                    best_remaining = remaining[i]
                    best_idx = i

            if best_idx is None:
                # No assignment can go here (all teachers busy or all done)
                slot_index += 1
                continue

            assignment = assignments[best_idx]
            teacher_id = assignment["tid"]
            course_id  = assignment["course_id"]

            # Find a free room
            room_id = None
            for rid in room_ids:
                if rid not in room_busy:
                    room_busy[rid] = set()
                if slot_id not in room_busy[rid]:
                    room_id = rid
                    break

            if not room_id:
                slot_index += 1
                continue

            # Schedule it
            cursor.execute('''
                INSERT INTO timetable_entries
                    (teacher_id,group_id,room_id,slot_id,course_id,semester,academic_year,status)
                VALUES (?,?,?,?,?,?,"2024-2025","scheduled")
            ''', (teacher_id, group_id, room_id, slot_id, course_id, request.semester))

            if teacher_id not in teacher_busy:
                teacher_busy[teacher_id] = set()
            teacher_busy[teacher_id].add(slot_id)
            room_busy[room_id].add(slot_id)
            group_busy.add(slot_id)

            entries_list.append({
                "day":          slot["day_name"],
                "time_slot":    f"{slot['start_time']}-{slot['end_time']}",
                "subject_code": assignment["course_code"],
                "subject_name": assignment["course_name"],
                "teacher_name": assignment["teacher_name"]
            })

            remaining[best_idx] -= 1
            assigned_count += 1
            slot_index += 1

            # If all done, stop
            if all(v <= 0 for v in remaining.values()):
                break

        timetable_data = json.dumps({
            "branch": request.branch, "year": request.year,
            "semester": request.semester, "section": request.section,
            "entries": entries_list, "days": DAYS, "time_slots": TIME_SLOTS,
            "generated_at": datetime.now().isoformat()
        })
        cursor.execute('''
            INSERT OR REPLACE INTO saved_timetables
                (branch,year,section,semester,timetable_data,generated_by,is_active)
            VALUES (?,?,?,?,?,?,1)
        ''', (request.branch, request.year, request.section, request.semester,
              timetable_data, current_user.get("user_id", 1)))

        for c in conflicts:
            cursor.execute(
                "INSERT INTO conflict_log (conflict_type,severity,conflict_description) VALUES (?,?,?)",
                (c["type"], "warning", c["description"]))

        conn.commit()

        unmet = {assignments[i]["course_code"]: remaining[i]
                 for i in range(len(assignments)) if remaining[i] > 0}
        msg = f"Timetable generated: {assigned_count} slots scheduled"
        if unmet:
            msg += f". Could not fit: {unmet} (teacher conflicts or insufficient slots)"

        return {
            "success": True,
            "message": msg,
            "assignments_scheduled": assigned_count,
            "conflicts_detected": len(conflicts),
            "unmet_hours": unmet
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ============================================================
# TIMETABLE VIEW
# ============================================================
async def _get_timetable(branch: str, year: int, section: str, semester: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timetable_data FROM saved_timetables
            WHERE branch=? AND year=? AND section=? AND semester=? AND is_active=1
            ORDER BY generated_at DESC LIMIT 1
        ''', (branch, year, section, semester))
        saved = cursor.fetchone()
        if saved:
            data = json.loads(saved["timetable_data"])
            return _build_timetable_response(branch, year, section, semester, [], data.get("entries", []))

        group_code = f"{branch}{year}{section}"
        cursor.execute("SELECT id FROM student_groups WHERE group_code=?", (group_code,))
        group_row = cursor.fetchone()
        if not group_row:
            return _build_timetable_response(branch, year, section, semester, [])

        cursor.execute('''
            SELECT te.*, ts.day_name, ts.start_time, ts.end_time,
                   c.course_code, c.course_name, t.name as teacher_name, r.room_code
            FROM timetable_entries te
            JOIN time_slots ts ON te.slot_id=ts.id
            JOIN courses c ON te.course_id=c.id
            JOIN teachers t ON te.teacher_id=t.id
            JOIN rooms r ON te.room_id=r.id
            WHERE te.group_id=? AND te.semester=? AND te.status="scheduled"
            ORDER BY ts.day_of_week, ts.start_time
        ''', (group_row["id"], semester))
        entries = [dict(r) for r in cursor.fetchall()]
        return _build_timetable_response(branch, year, section, semester, entries)
    finally:
        conn.close()

@app.get("/api/timetable/view")
async def view_timetable_query(
    branch: str, year: int, section: str, semester: int = 1,
    current_user=Depends(get_current_user)
):
    return await _get_timetable(branch, year, section, semester)

@app.get("/api/timetable/view/{branch}/{year}/{section}")
async def view_timetable_path(
    branch: str, year: int, section: str, semester: int = 1,
    current_user=Depends(get_current_user)
):
    return await _get_timetable(branch, year, section, semester)


# ============================================================
# CONFLICTS
# ============================================================
@app.get("/api/conflicts")
async def get_conflicts(resolved: bool = False, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conflict_log WHERE resolved=? ORDER BY created_at DESC", (1 if resolved else 0,))
        conflicts = [dict(r) for r in cursor.fetchall()]
        return {"conflicts": conflicts, "count": len(conflicts)}
    finally:
        conn.close()

@app.post("/api/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: int, request: ConflictResolveRequest, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE conflict_log SET resolved=1, resolved_at=CURRENT_TIMESTAMP WHERE id=?", (conflict_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conflict not found")
        conn.commit()
        return {"success": True, "message": "Conflict resolved"}
    finally:
        conn.close()


# ============================================================
# STATS
# ============================================================
@app.get("/api/stats")
async def get_stats(_=Depends(get_current_user)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        stats = {}
        for key, table, where in [
            ("teachers",          "teachers",          "WHERE is_active=1"),
            ("groups",            "student_groups",    "WHERE is_active=1"),
            ("rooms",             "rooms",             "WHERE is_active=1"),
            ("courses",           "courses",           ""),
            ("subjects",          "subjects",          ""),
            ("timetable_entries", "timetable_entries", 'WHERE status="scheduled"'),
            ("conflicts",         "conflict_log",      "WHERE resolved=0"),
            ("saved_timetables",  "saved_timetables",  "WHERE is_active=1"),
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table} {where}")
            stats[key] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()


# ============================================================
# HOLIDAYS
# ============================================================
@app.get("/api/holidays")
async def get_holidays():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM holidays ORDER BY holiday_date")
        return {"holidays": [dict(r) for r in cursor.fetchall()]}
    finally:
        conn.close()

@app.post("/api/admin/holidays")
async def add_holiday(data: dict, _=Depends(require_admin)):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO holidays (holiday_name,holiday_date,is_optional,description) VALUES (?,?,?,?)",
            (data.get("name"), data.get("date"), data.get("is_optional", 0), data.get("description")))
        conn.commit()
        return {"success": True, "message": "Holiday added"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎓 SGSITS Timetable API v4.0")
    print("=" * 60)
    print("📍 Server  : http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print("🔐 Credentials:")
    print("   Admin   : admin   / admin123")
    print("   Teacher : teacher / teacher123")
    print("   Student : student / student123")
    print("=" * 60)
    print("📋 All frontend → backend routes:")
    print("   AddTeacher    → GET/POST /api/admin/teachers")
    print("   AddSubject    → GET /api/admin/teachers")
    print("                 → POST /api/admin/subjects")
    print("   AssignSubject → GET /api/admin/subjects?branch=&year=")
    print("                 → GET /api/admin/teachers")
    print("                 → POST /api/admin/subjects/assign")
    print("   GenerateTT    → POST /api/timetable/generate")
    print("                 → GET  /api/timetable/view?branch=&year=&section=&semester=")
    print("   ViewTimetable → GET  /api/timetable/view?branch=&year=&section=")
    print("   StudentDash   → GET  /api/timetable/view?branch=&year=&section=")
    print("   TeacherSched  → GET  /api/teachers/{id}/schedule")
    print("   AdminUsers    → GET  /api/admin/users")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)