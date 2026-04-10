# backend/database.py - Complete SQLite Database for Timetable Generator
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "timetable.db")

@contextmanager
def get_db():
    """Get database connection with context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize all database tables with complete schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # ============================================================
        # 1. USERS & AUTHENTICATION TABLES
        # ============================================================
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT CHECK(role IN ('admin', 'teacher', 'student')) DEFAULT 'student',
                is_active BOOLEAN DEFAULT 1,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # ============================================================
        # 2. TEACHER/FACULTY TABLES
        # ============================================================
        
        # Teachers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                teacher_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                designation TEXT,
                specialization TEXT,
                joining_date DATE,
                max_hours_per_day INTEGER DEFAULT 6,
                max_hours_per_week INTEGER DEFAULT 24,
                preferred_days TEXT,  -- JSON array: [0,1,2,3,4] (0=Monday)
                preferred_times TEXT,  -- JSON array: ["09:00", "10:00", "11:00"]
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
        
        # Teacher availability (unavailable times - they CANNOT teach)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_unavailability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,  -- 0=Monday, 1=Tuesday, etc.
                slot_id INTEGER,
                start_date DATE,
                end_date DATE,
                reason TEXT,
                is_recurring BOOLEAN DEFAULT 0,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (slot_id) REFERENCES time_slots(id) ON DELETE SET NULL
            )
        ''')
        
        # Teacher preferences (soft constraints)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                preference_type TEXT CHECK(preference_type IN ('preferred_day', 'preferred_time', 'avoid_day', 'avoid_time', 'preferred_room')),
                preference_value TEXT,
                priority INTEGER DEFAULT 1,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            )
        ''')
        
        # ============================================================
        # 3. STUDENT & CLASS TABLES
        # ============================================================
        
        # Student groups (divisions/sections)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_code TEXT UNIQUE NOT NULL,
                group_name TEXT NOT NULL,
                semester INTEGER NOT NULL,
                department TEXT NOT NULL,
                academic_year TEXT,
                student_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                student_id TEXT UNIQUE NOT NULL,
                roll_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                group_id INTEGER NOT NULL,
                enrollment_year INTEGER,
                parent_phone TEXT,
                address TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (group_id) REFERENCES student_groups(id) ON DELETE CASCADE
            )
        ''')
        
        # ============================================================
        # 4. COURSE & SUBJECT TABLES
        # ============================================================
        
        # Courses/Subjects master table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                description TEXT,
                credits INTEGER DEFAULT 3,
                hours_per_week INTEGER DEFAULT 3,
                theory_hours INTEGER DEFAULT 2,
                lab_hours INTEGER DEFAULT 1,
                tutorial_hours INTEGER DEFAULT 0,
                is_lab BOOLEAN DEFAULT 0,
                is_elective BOOLEAN DEFAULT 0,
                department TEXT,
                semester INTEGER,
                prerequisites TEXT,  -- JSON array of course codes
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Course assignments (which teacher teaches which course to which group)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                semester INTEGER NOT NULL,
                academic_year TEXT NOT NULL,
                hours_per_week INTEGER,
                theory_hours INTEGER,
                lab_hours INTEGER,
                is_lab BOOLEAN DEFAULT 0,
                preferred_room TEXT,
                preferred_slots TEXT,  -- JSON array of slot IDs
                priority INTEGER DEFAULT 1,
                is_elective BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES student_groups(id) ON DELETE CASCADE,
                UNIQUE(course_id, teacher_id, group_id, semester, academic_year)
            )
        ''')
        
        # ============================================================
        # 5. ROOM & FACILITY TABLES
        # ============================================================
        
        # Rooms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT UNIQUE NOT NULL,
                room_name TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                room_type TEXT CHECK(room_type IN ('lecture', 'lab', 'auditorium', 'seminar_hall')) DEFAULT 'lecture',
                building TEXT,
                floor INTEGER,
                has_projector BOOLEAN DEFAULT 0,
                has_whiteboard BOOLEAN DEFAULT 1,
                has_ac BOOLEAN DEFAULT 0,
                has_computers BOOLEAN DEFAULT 0,
                has_smartboard BOOLEAN DEFAULT 0,
                has_wifi BOOLEAN DEFAULT 0,
                is_lab BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Room features (extensible)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                feature_name TEXT NOT NULL,
                feature_value TEXT,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        ''')
        
        # Room unavailability (maintenance, events, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_unavailability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                day_of_week INTEGER,
                slot_id INTEGER,
                start_date DATE,
                end_date DATE,
                reason TEXT,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (slot_id) REFERENCES time_slots(id) ON DELETE SET NULL
            )
        ''')
        
        # ============================================================
        # 6. TIME SLOT TABLES
        # ============================================================
        
        # Time slots master table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_code TEXT UNIQUE NOT NULL,
                slot_name TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,  -- 0=Monday to 6=Sunday
                day_name TEXT NOT NULL,
                start_time TEXT NOT NULL,  -- HH:MM format
                end_time TEXT NOT NULL,
                duration INTEGER,  -- in minutes
                slot_type TEXT CHECK(slot_type IN ('lecture', 'lab', 'break', 'library')) DEFAULT 'lecture',
                is_break BOOLEAN DEFAULT 0,
                academic_year TEXT,
                semester INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ============================================================
        # 7. TIMETABLE ENTRIES (THE ACTUAL SCHEDULE)
        # ============================================================
        
        # Main timetable entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timetable_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_assignment_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                slot_id INTEGER NOT NULL,
                semester INTEGER NOT NULL,
                academic_year TEXT NOT NULL,
                week_number INTEGER DEFAULT 1,
                is_makeup BOOLEAN DEFAULT 0,
                original_slot_id INTEGER,
                status TEXT CHECK(status IN ('scheduled', 'cancelled', 'rescheduled', 'completed')) DEFAULT 'scheduled',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_assignment_id) REFERENCES course_assignments(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES student_groups(id) ON DELETE CASCADE,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (slot_id) REFERENCES time_slots(id) ON DELETE CASCADE,
                UNIQUE(teacher_id, slot_id, week_number, academic_year),
                UNIQUE(room_id, slot_id, week_number, academic_year),
                UNIQUE(group_id, slot_id, week_number, academic_year)
            )
        ''')
        
        # Timetable history for auditing changes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timetable_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timetable_entry_id INTEGER,
                action TEXT CHECK(action IN ('CREATE', 'UPDATE', 'DELETE', 'RESCHEDULE')),
                old_data TEXT,  -- JSON
                new_data TEXT,  -- JSON
                changed_by INTEGER,
                reason TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (timetable_entry_id) REFERENCES timetable_entries(id) ON DELETE SET NULL
            )
        ''')
        
        # ============================================================
        # 8. CONFLICT & CONSTRAINT TABLES
        # ============================================================
        
        # Conflict log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_type TEXT CHECK(conflict_type IN ('teacher', 'room', 'group', 'capacity', 'time')),
                severity TEXT CHECK(severity IN ('critical', 'warning', 'info')) DEFAULT 'warning',
                teacher_id INTEGER,
                group_id INTEGER,
                room_id INTEGER,
                slot_id INTEGER,
                conflict_description TEXT,
                suggested_resolution TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolved_at TIMESTAMP,
                resolved_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL,
                FOREIGN KEY (group_id) REFERENCES student_groups(id) ON DELETE SET NULL,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
                FOREIGN KEY (slot_id) REFERENCES time_slots(id) ON DELETE SET NULL
            )
        ''')
        
        # ============================================================
        # 9. ACADEMIC CALENDAR
        # ============================================================
        
        # Academic calendar
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS academic_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                academic_year TEXT NOT NULL,
                semester INTEGER NOT NULL,
                event_name TEXT NOT NULL,
                event_type TEXT CHECK(event_type IN ('start', 'end', 'holiday', 'exam', 'break')),
                start_date DATE NOT NULL,
                end_date DATE,
                description TEXT,
                UNIQUE(academic_year, semester, start_date)
            )
        ''')
        
        # Holidays
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holiday_name TEXT NOT NULL,
                holiday_date DATE UNIQUE NOT NULL,
                is_optional BOOLEAN DEFAULT 0,
                description TEXT
            )
        ''')
        
        # ============================================================
        # 10. INDEXES FOR PERFORMANCE
        # ============================================================
        
        # User indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        
        # Teacher indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_teachers_email ON teachers(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_teachers_department ON teachers(department)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_teachers_code ON teachers(teacher_code)')
        
        # Student indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_email ON students(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_group ON students(group_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_number)')
        
        # Course indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department)')
        
        # Course assignments indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ca_teacher ON course_assignments(teacher_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ca_group ON course_assignments(group_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ca_course ON course_assignments(course_id)')
        
        # Timetable indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tt_teacher ON timetable_entries(teacher_id, slot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tt_group ON timetable_entries(group_id, slot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tt_room ON timetable_entries(room_id, slot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tt_semester ON timetable_entries(semester)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tt_academic_year ON timetable_entries(academic_year)')
        
        # Time slots indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_slots_day ON time_slots(day_of_week)')
        
        # Conflict log indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conflicts_resolved ON conflict_log(resolved)')
        
        print("✅ All database tables created successfully!")
        
        # Insert sample data
        insert_sample_data(cursor)

def insert_sample_data(cursor):
    """Insert comprehensive sample data for testing"""
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        print("📊 Sample data already exists, skipping...")
        return
    
    print("📝 Inserting sample data...")
    
    # ============ 1. USERS ============
    users = [
        ("admin", "admin@timetable.com", "admin123", "System Administrator", "admin"),
        ("teacher_abhijeet", "abhijeet@timetable.com", "teacher123", "Prof. Abhijeet", "teacher"),
        ("teacher_subhit", "subhit@timetable.com", "teacher123", "Prof. Subhit", "teacher"),
        ("teacher_sharma", "sharma@timetable.com", "teacher123", "Prof. Sharma", "teacher"),
        ("teacher_patel", "patel@timetable.com", "teacher123", "Prof. Patel", "teacher"),
        ("student1", "student1@timetable.com", "student123", "John Doe", "student"),
        ("student2", "student2@timetable.com", "student123", "Jane Smith", "student"),
    ]
    
    for username, email, pwd, name, role in users:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (username, email, pwd, name, role))
    
    # ============ 2. TEACHERS ============
    teachers = [
        ("T001", "Prof. Abhijeet", "abhijeet@timetable.com", "CSE", "Professor", "Electrical Engineering", 6, 24, None, None),
        ("T002", "Prof. Subhit", "subhit@timetable.com", "Mathematics", "Associate Professor", "Applied Mathematics", 6, 24, None, None),
        ("T003", "Prof. Sharma", "sharma@timetable.com", "Physics", "Professor", "Quantum Physics", 5, 20, None, None),
        ("T004", "Prof. Patel", "patel@timetable.com", "Chemistry", "Assistant Professor", "Organic Chemistry", 5, 20, None, None),
        ("T005", "Prof. Kumar", "kumar@timetable.com", "CSE", "Professor", "Data Structures", 6, 24, None, None),
    ]
    
    for code, name, email, dept, desig, spec, max_day, max_week, pref_days, pref_times in teachers:
        cursor.execute('''
            INSERT INTO teachers (teacher_code, name, email, department, designation, specialization, 
                                  max_hours_per_day, max_hours_per_week, preferred_days, preferred_times, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (code, name, email, dept, desig, spec, max_day, max_week, pref_days, pref_times))
    
    # ============ 3. STUDENT GROUPS ============
    groups = [
        ("SEA", "SE Computer A", 3, "CSE", "2024-2025", 60),
        ("SEB", "SE Computer B", 3, "CSE", "2024-2025", 58),
        ("TEA", "TE Computer A", 5, "CSE", "2024-2025", 55),
        ("TEB", "TE Computer B", 5, "CSE", "2024-2025", 53),
        ("TMA", "TE Mechanical A", 5, "ME", "2024-2025", 50),
        ("TMB", "TE Mechanical B", 5, "ME", "2024-2025", 48),
    ]
    
    for code, name, sem, dept, year, count in groups:
        cursor.execute('''
            INSERT INTO student_groups (group_code, group_name, semester, department, academic_year, student_count, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (code, name, sem, dept, year, count))
    
    # ============ 4. ROOMS ============
    rooms = [
        ("R101", "Room 101", 60, "lecture", "Main Building", 1, 1, 1, 1, 0, 1, 0),
        ("R102", "Room 102", 50, "lecture", "Main Building", 1, 0, 1, 0, 0, 0, 0),
        ("R103", "Room 103", 50, "lecture", "Main Building", 1, 0, 1, 0, 0, 0, 0),
        ("R201", "Room 201", 80, "lecture", "Main Building", 2, 1, 1, 1, 0, 1, 0),
        ("R202", "Room 202", 70, "lecture", "Main Building", 2, 1, 1, 1, 0, 1, 0),
        ("LAB1", "Computer Lab 1", 40, "lab", "Lab Block", 1, 1, 0, 0, 1, 1, 1),
        ("LAB2", "Computer Lab 2", 40, "lab", "Lab Block", 1, 1, 0, 0, 1, 1, 1),
        ("LAB3", "Chemistry Lab", 40, "lab", "Science Block", 1, 1, 0, 0, 1, 0, 1),
        ("LAB4", "Physics Lab", 40, "lab", "Science Block", 1, 1, 0, 0, 1, 0, 1),
        ("AUD1", "Auditorium", 200, "auditorium", "Main Building", 1, 1, 1, 1, 1, 1, 0),
    ]
    
    for code, name, cap, rtype, building, floor, proj, board, ac, comp, smart, lab in rooms:
        cursor.execute('''
            INSERT INTO rooms (room_code, room_name, capacity, room_type, building, floor, 
                              has_projector, has_whiteboard, has_ac, has_computers, has_smartboard, is_lab, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (code, name, cap, rtype, building, floor, proj, board, ac, comp, smart, lab))
    
    # ============ 5. TIME SLOTS (FIXED VERSION) ============
    days = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday")
    ]
    
    # Define time slots with proper structure: (slot_code, start_time, end_time, duration, slot_type, is_break)
    time_slot_definitions = [
        ("S1", "08:00", "09:00", 60, "lecture", 0),
        ("S2", "09:00", "10:00", 60, "lecture", 0),
        ("S3", "10:00", "11:00", 60, "lecture", 0),
        ("S4", "11:00", "12:00", 60, "lecture", 0),
        ("S5", "12:00", "13:00", 60, "lecture", 0),
        ("Break1", "13:00", "14:00", 60, "break", 1),
        ("S6", "14:00", "15:00", 60, "lecture", 0),
        ("S7", "15:00", "16:00", 60, "lecture", 0),
        ("S8", "16:00", "17:00", 60, "lecture", 0),
    ]
    
    slot_id = 1
    for day_idx, day_name in days:
        for slot_def in time_slot_definitions:
            code, start, end, duration, slot_type, is_break = slot_def
            
            cursor.execute('''
                INSERT INTO time_slots (id, slot_code, slot_name, day_of_week, day_name, 
                                       start_time, end_time, duration, slot_type, is_break, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (slot_id, f"{day_name[:3]}{code}", f"{day_name[:3]} {start}-{end}", 
                  day_idx, day_name, start, end, duration, slot_type, is_break))
            slot_id += 1
    
    # ============ 6. COURSES ============
    courses = [
        ("BEE101", "Basic Electrical Engineering", "Introduction to electrical circuits and systems", 3, 3, 2, 1, 0, 0, "CSE", 3, None),
        ("MATH201", "Mathematics 2", "Calculus and Linear Algebra", 4, 4, 3, 1, 0, 0, "Mathematics", 3, None),
        ("PHY101", "Engineering Physics", "Physics for engineers", 3, 3, 2, 1, 0, 0, "Physics", 3, None),
        ("PHY101L", "Engineering Physics Lab", "Physics laboratory", 1, 2, 0, 2, 0, 1, "Physics", 3, None),
        ("CS201", "Data Structures", "Data structures and algorithms", 4, 4, 3, 1, 0, 0, "CSE", 5, None),
        ("CS201L", "Data Structures Lab", "Programming lab for data structures", 1, 2, 0, 2, 0, 1, "CSE", 5, None),
        ("CHEM101", "Organic Chemistry", "Basic organic chemistry", 3, 3, 2, 1, 0, 0, "Chemistry", 3, None),
        ("CHEM101L", "Chemistry Lab", "Chemistry laboratory", 1, 2, 0, 2, 0, 1, "Chemistry", 3, None),
        ("ME101", "Engineering Mechanics", "Mechanics for engineers", 3, 3, 2, 1, 0, 0, "ME", 3, None),
        ("HS101", "Communication Skills", "Professional communication", 2, 2, 2, 0, 0, 0, "Humanities", 3, None),
    ]
    
    for code, name, desc, credits, hours, theory, lab, tut, is_lab, dept, sem, prereq in courses:
        cursor.execute('''
            INSERT INTO courses (course_code, course_name, description, credits, hours_per_week,
                                theory_hours, lab_hours, tutorial_hours, is_lab, department, semester, prerequisites)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, desc, credits, hours, theory, lab, tut, is_lab, dept, sem, prereq))
    
    # ============ 7. COURSE ASSIGNMENTS ============
    assignments = [
        (1, 1, 1, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # BEE101 - Abhijeet - SEA
        (1, 1, 2, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # BEE101 - Abhijeet - SEB
        (2, 2, 1, 3, "2024-2025", 4, 3, 1, 0, None, None, 2, 0),  # MATH201 - Subhit - SEA
        (2, 2, 2, 3, "2024-2025", 4, 3, 1, 0, None, None, 2, 0),  # MATH201 - Subhit - SEB
        (3, 3, 1, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # PHY101 - Sharma - SEA
        (4, 3, 1, 3, "2024-2025", 2, 0, 2, 1, "LAB4", None, 3, 0),  # PHY101L - Sharma - SEA
        (5, 5, 3, 5, "2024-2025", 4, 3, 1, 0, "R201", None, 2, 0),  # CS201 - Kumar - TEA
        (6, 5, 3, 5, "2024-2025", 2, 0, 2, 1, "LAB1", None, 3, 0),  # CS201L - Kumar - TEA
        (7, 4, 4, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # CHEM101 - Patel - TEA
        (8, 4, 4, 3, "2024-2025", 2, 0, 2, 1, "LAB3", None, 3, 0),  # CHEM101L - Patel - TEA
    ]
    
    for course_id, teacher_id, group_id, sem, year, hours, theory, lab, is_lab, room, slots, priority, elective in assignments:
        cursor.execute('''
            INSERT INTO course_assignments (course_id, teacher_id, group_id, semester, academic_year,
                                           hours_per_week, theory_hours, lab_hours, is_lab, preferred_room,
                                           preferred_slots, priority, is_elective)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (course_id, teacher_id, group_id, sem, year, hours, theory, lab, is_lab, room, slots, priority, elective))
    
    # ============ 8. ACADEMIC CALENDAR ============
    calendar_events = [
        ("2024-2025", 3, "Semester Start", "start", "2024-07-15", None),
        ("2024-2025", 3, "Mid Semester Exams", "exam", "2024-09-01", "2024-09-10"),
        ("2024-2025", 3, "Semester End", "end", "2024-11-30", None),
        ("2024-2025", 3, "Diwali Break", "break", "2024-10-20", "2024-10-27"),
    ]
    
    for year, sem, name, etype, start, end in calendar_events:
        cursor.execute('''
            INSERT INTO academic_calendar (academic_year, semester, event_name, event_type, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (year, sem, name, etype, start, end))
    
    # ============ 9. HOLIDAYS ============
    holidays = [
        ("Republic Day", "2024-01-26", 0),
        ("Holi", "2024-03-25", 0),
        ("Independence Day", "2024-08-15", 0),
        ("Gandhi Jayanti", "2024-10-02", 0),
        ("Christmas", "2024-12-25", 0),
    ]
    
    for name, date, optional in holidays:
        cursor.execute('''
            INSERT INTO holidays (holiday_name, holiday_date, is_optional)
            VALUES (?, ?, ?)
        ''', (name, date, optional))
    
    print("✅ Sample data inserted successfully!")
    print(f"   - {len(users)} users")
    print(f"   - {len(teachers)} teachers")
    print(f"   - {len(groups)} student groups")
    print(f"   - {len(rooms)} rooms")
    print(f"   - {slot_id - 1} time slots")
    print(f"   - {len(courses)} courses")
    print(f"   - {len(assignments)} course assignments")
    """Insert comprehensive sample data for testing"""
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        print("📊 Sample data already exists, skipping...")
        return
    
    print("📝 Inserting sample data...")
    
    # ============ 1. USERS ============
    users = [
        ("admin", "admin@timetable.com", "admin123", "System Administrator", "admin"),
        ("teacher_abhijeet", "abhijeet@timetable.com", "teacher123", "Prof. Abhijeet", "teacher"),
        ("teacher_subhit", "subhit@timetable.com", "teacher123", "Prof. Subhit", "teacher"),
        ("teacher_sharma", "sharma@timetable.com", "teacher123", "Prof. Sharma", "teacher"),
        ("teacher_patel", "patel@timetable.com", "teacher123", "Prof. Patel", "teacher"),
        ("student1", "student1@timetable.com", "student123", "John Doe", "student"),
        ("student2", "student2@timetable.com", "student123", "Jane Smith", "student"),
    ]
    
    for username, email, pwd, name, role in users:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (username, email, pwd, name, role))
    
    # ============ 2. TEACHERS ============
    teachers = [
        ("T001", "Prof. Abhijeet", "abhijeet@timetable.com", "CSE", "Professor", "Electrical Engineering", 6, 24, None, None),
        ("T002", "Prof. Subhit", "subhit@timetable.com", "Mathematics", "Associate Professor", "Applied Mathematics", 6, 24, None, None),
        ("T003", "Prof. Sharma", "sharma@timetable.com", "Physics", "Professor", "Quantum Physics", 5, 20, None, None),
        ("T004", "Prof. Patel", "patel@timetable.com", "Chemistry", "Assistant Professor", "Organic Chemistry", 5, 20, None, None),
        ("T005", "Prof. Kumar", "kumar@timetable.com", "CSE", "Professor", "Data Structures", 6, 24, None, None),
    ]
    
    for code, name, email, dept, desig, spec, max_day, max_week, pref_days, pref_times in teachers:
        cursor.execute('''
            INSERT INTO teachers (teacher_code, name, email, department, designation, specialization, 
                                  max_hours_per_day, max_hours_per_week, preferred_days, preferred_times, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (code, name, email, dept, desig, spec, max_day, max_week, pref_days, pref_times))
    
    # ============ 3. STUDENT GROUPS ============
    groups = [
        ("SEA", "SE Computer A", 3, "CSE", "2024-2025", 60),
        ("SEB", "SE Computer B", 3, "CSE", "2024-2025", 58),
        ("TEA", "TE Computer A", 5, "CSE", "2024-2025", 55),
        ("TEB", "TE Computer B", 5, "CSE", "2024-2025", 53),
        ("TMA", "TE Mechanical A", 5, "ME", "2024-2025", 50),
        ("TMB", "TE Mechanical B", 5, "ME", "2024-2025", 48),
    ]
    
    for code, name, sem, dept, year, count in groups:
        cursor.execute('''
            INSERT INTO student_groups (group_code, group_name, semester, department, academic_year, student_count, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (code, name, sem, dept, year, count))
    
    # ============ 4. ROOMS ============
    rooms = [
        ("R101", "Room 101", 60, "lecture", "Main Building", 1, 1, 1, 1, 0, 1, 0),
        ("R102", "Room 102", 50, "lecture", "Main Building", 1, 0, 1, 0, 0, 0, 0),
        ("R103", "Room 103", 50, "lecture", "Main Building", 1, 0, 1, 0, 0, 0, 0),
        ("R201", "Room 201", 80, "lecture", "Main Building", 2, 1, 1, 1, 0, 1, 0),
        ("R202", "Room 202", 70, "lecture", "Main Building", 2, 1, 1, 1, 0, 1, 0),
        ("LAB1", "Computer Lab 1", 40, "lab", "Lab Block", 1, 1, 0, 0, 1, 1, 1),
        ("LAB2", "Computer Lab 2", 40, "lab", "Lab Block", 1, 1, 0, 0, 1, 1, 1),
        ("LAB3", "Chemistry Lab", 40, "lab", "Science Block", 1, 1, 0, 0, 1, 0, 1),
        ("LAB4", "Physics Lab", 40, "lab", "Science Block", 1, 1, 0, 0, 1, 0, 1),
        ("AUD1", "Auditorium", 200, "auditorium", "Main Building", 1, 1, 1, 1, 1, 1, 0),
    ]
    
    for code, name, cap, rtype, building, floor, proj, board, ac, comp, smart, lab in rooms:
        cursor.execute('''
            INSERT INTO rooms (room_code, room_name, capacity, room_type, building, floor, 
                              has_projector, has_whiteboard, has_ac, has_computers, has_smartboard, is_lab, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (code, name, cap, rtype, building, floor, proj, board, ac, comp, smart, lab))
    
    # ============ 5. TIME SLOTS ============
    days = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday")
    ]
    times = [
        ("S1", "08:00", "09:00", 60), ("S2", "09:00", "10:00", 60),
        ("S3", "10:00", "11:00", 60), ("S4", "11:00", "12:00", 60),
        ("S5", "12:00", "13:00", 60), ("Break1", "13:00", "14:00", 60, "break", 1),
        ("S6", "14:00", "15:00", 60), ("S7", "15:00", "16:00", 60),
        ("S8", "16:00", "17:00", 60),
    ]
    
    slot_id = 1
    for day_idx, day_name in days:
        for time_data in times:
            if len(time_data) == 5:
                code, start, end, dur, stype, is_break = time_data
            elif len(time_data) == 4:
                code, start, end, dur = time_data
                stype = "lecture"
                is_break = 0
            else:
                code, start, end, dur, stype = time_data
                is_break = 1 if stype == "break" else 0
            
            cursor.execute('''
                INSERT INTO time_slots (id, slot_code, slot_name, day_of_week, day_name, 
                                       start_time, end_time, duration, slot_type, is_break, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (slot_id, f"{day_name[:3]}{code}", f"{day_name[:3]} {start}-{end}", 
                  day_idx, day_name, start, end, dur, stype, is_break))
            slot_id += 1
    
    # ============ 6. COURSES ============
    courses = [
        ("BEE101", "Basic Electrical Engineering", "Introduction to electrical circuits and systems", 3, 3, 2, 1, 0, 0, "CSE", 3, None),
        ("MATH201", "Mathematics 2", "Calculus and Linear Algebra", 4, 4, 3, 1, 0, 0, "Mathematics", 3, None),
        ("PHY101", "Engineering Physics", "Physics for engineers", 3, 3, 2, 1, 0, 0, "Physics", 3, None),
        ("PHY101L", "Engineering Physics Lab", "Physics laboratory", 1, 2, 0, 2, 0, 1, "Physics", 3, None),
        ("CS201", "Data Structures", "Data structures and algorithms", 4, 4, 3, 1, 0, 0, "CSE", 5, None),
        ("CS201L", "Data Structures Lab", "Programming lab for data structures", 1, 2, 0, 2, 0, 1, "CSE", 5, None),
        ("CHEM101", "Organic Chemistry", "Basic organic chemistry", 3, 3, 2, 1, 0, 0, "Chemistry", 3, None),
        ("CHEM101L", "Chemistry Lab", "Chemistry laboratory", 1, 2, 0, 2, 0, 1, "Chemistry", 3, None),
        ("ME101", "Engineering Mechanics", "Mechanics for engineers", 3, 3, 2, 1, 0, 0, "ME", 3, None),
        ("HS101", "Communication Skills", "Professional communication", 2, 2, 2, 0, 0, 0, "Humanities", 3, None),
    ]
    
    for code, name, desc, credits, hours, theory, lab, tut, is_lab, dept, sem, prereq in courses:
        cursor.execute('''
            INSERT INTO courses (course_code, course_name, description, credits, hours_per_week,
                                theory_hours, lab_hours, tutorial_hours, is_lab, department, semester, prerequisites)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, desc, credits, hours, theory, lab, tut, is_lab, dept, sem, prereq))
    
    # ============ 7. COURSE ASSIGNMENTS ============
    assignments = [
        (1, 1, 1, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # BEE101 - Abhijeet - SEA
        (1, 1, 2, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # BEE101 - Abhijeet - SEB
        (2, 2, 1, 3, "2024-2025", 4, 3, 1, 0, None, None, 2, 0),  # MATH201 - Subhit - SEA
        (2, 2, 2, 3, "2024-2025", 4, 3, 1, 0, None, None, 2, 0),  # MATH201 - Subhit - SEB
        (3, 3, 1, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # PHY101 - Sharma - SEA
        (4, 3, 1, 3, "2024-2025", 2, 0, 2, 1, "LAB4", None, 3, 0),  # PHY101L - Sharma - SEA
        (5, 5, 3, 5, "2024-2025", 4, 3, 1, 0, "R201", None, 2, 0),  # CS201 - Kumar - TEA
        (6, 5, 3, 5, "2024-2025", 2, 0, 2, 1, "LAB1", None, 3, 0),  # CS201L - Kumar - TEA
        (7, 4, 4, 3, "2024-2025", 3, 2, 1, 0, None, None, 1, 0),  # CHEM101 - Patel - TEA
        (8, 4, 4, 3, "2024-2025", 2, 0, 2, 1, "LAB3", None, 3, 0),  # CHEM101L - Patel - TEA
    ]
    
    for course_id, teacher_id, group_id, sem, year, hours, theory, lab, is_lab, room, slots, priority, elective in assignments:
        cursor.execute('''
            INSERT INTO course_assignments (course_id, teacher_id, group_id, semester, academic_year,
                                           hours_per_week, theory_hours, lab_hours, is_lab, preferred_room,
                                           preferred_slots, priority, is_elective)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (course_id, teacher_id, group_id, sem, year, hours, theory, lab, is_lab, room, slots, priority, elective))
    
    # ============ 8. ACADEMIC CALENDAR ============
    calendar_events = [
        ("2024-2025", 3, "Semester Start", "start", "2024-07-15", None),
        ("2024-2025", 3, "Mid Semester Exams", "exam", "2024-09-01", "2024-09-10"),
        ("2024-2025", 3, "Semester End", "end", "2024-11-30", None),
        ("2024-2025", 3, "Diwali Break", "break", "2024-10-20", "2024-10-27"),
    ]
    
    for year, sem, name, etype, start, end in calendar_events:
        cursor.execute('''
            INSERT INTO academic_calendar (academic_year, semester, event_name, event_type, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (year, sem, name, etype, start, end))
    
    # ============ 9. HOLIDAYS ============
    holidays = [
        ("Republic Day", "2024-01-26", 0),
        ("Holi", "2024-03-25", 0),
        ("Independence Day", "2024-08-15", 0),
        ("Gandhi Jayanti", "2024-10-02", 0),
        ("Christmas", "2024-12-25", 0),
    ]
    
    for name, date, optional in holidays:
        cursor.execute('''
            INSERT INTO holidays (holiday_name, holiday_date, is_optional)
            VALUES (?, ?, ?)
        ''', (name, date, optional))
    
    print("✅ Sample data inserted successfully!")
    print(f"   - {len(users)} users")
    print(f"   - {len(teachers)} teachers")
    print(f"   - {len(groups)} student groups")
    print(f"   - {len(rooms)} rooms")
    print(f"   - {slot_id - 1} time slots")
    print(f"   - {len(courses)} courses")
    print(f"   - {len(assignments)} course assignments")

# Initialize database when module loads
if __name__ == "__main__":
    init_db()
    print("\n🎉 Database setup complete!")
    print(f"📁 Database location: {DB_PATH}")
else:
    init_db()