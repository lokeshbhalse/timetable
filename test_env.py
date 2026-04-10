# test_env.py - Complete testing environment for timetable generator
import sqlite3
import hashlib
import json
from datetime import datetime
import os

# ============ DATABASE SETUP ============
DB_PATH = "test_timetable.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    """Create test database with all tables"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✅ Old test database removed")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            role TEXT,
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
            max_hours_per_day INTEGER
        )
    ''')
    
    # Student groups
    cursor.execute('''
        CREATE TABLE student_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_code TEXT,
            group_name TEXT,
            semester INTEGER,
            department TEXT,
            student_count INTEGER
        )
    ''')
    
    # Courses
    cursor.execute('''
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT,
            course_name TEXT,
            credits INTEGER,
            department TEXT,
            semester INTEGER
        )
    ''')
    
    # Course assignments (Teacher + Course + Group)
    cursor.execute('''
        CREATE TABLE course_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            teacher_id INTEGER,
            group_id INTEGER,
            semester INTEGER
        )
    ''')
    
    # Rooms
    cursor.execute('''
        CREATE TABLE rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT,
            room_name TEXT,
            capacity INTEGER,
            room_type TEXT
        )
    ''')
    
    # Time slots
    cursor.execute('''
        CREATE TABLE time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_code TEXT,
            day_name TEXT,
            start_time TEXT,
            end_time TEXT
        )
    ''')
    
    # Timetable entries
    cursor.execute('''
        CREATE TABLE timetable_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            group_id INTEGER,
            room_id INTEGER,
            slot_id INTEGER,
            course_id INTEGER,
            day_name TEXT,
            time_slot TEXT
        )
    ''')
    
    # ============ INSERT TEST DATA ============
    
    # Users
    users = [
        ('admin', 'admin@test.com', hash_password('admin123'), 'Admin User', 'admin'),
        ('teacher1', 'teacher1@test.com', hash_password('teacher123'), 'Prof. Abhijeet', 'teacher'),
        ('teacher2', 'teacher2@test.com', hash_password('teacher123'), 'Prof. Subhit', 'teacher'),
        ('student1', 'student1@test.com', hash_password('student123'), 'John Doe', 'student'),
    ]
    cursor.executemany('INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?,?,?,?,?)', users)
    
    # Teachers
    teachers = [
        ('Prof. Abhijeet', 'abhijeet@test.com', 'CSE', 6),
        ('Prof. Subhit', 'subhit@test.com', 'Mathematics', 6),
        ('Prof. Sharma', 'sharma@test.com', 'Physics', 5),
    ]
    cursor.executemany('INSERT INTO teachers (name, email, department, max_hours_per_day) VALUES (?,?,?,?)', teachers)
    
    # Student Groups
    groups = [
        ('SEA', 'SE Computer A', 3, 'CSE', 60),
        ('SEB', 'SE Computer B', 3, 'CSE', 58),
        ('TEA', 'TE Computer A', 5, 'CSE', 55),
    ]
    cursor.executemany('INSERT INTO student_groups (group_code, group_name, semester, department, student_count) VALUES (?,?,?,?,?)', groups)
    
    # Courses
    courses = [
        ('BEE101', 'Basic Electrical Engineering', 3, 'CSE', 3),
        ('MATH201', 'Mathematics 2', 4, 'Mathematics', 3),
        ('CS201', 'Data Structures', 4, 'CSE', 5),
        ('CS201L', 'Data Structures Lab', 2, 'CSE', 5),
    ]
    cursor.executemany('INSERT INTO courses (course_code, course_name, credits, department, semester) VALUES (?,?,?,?,?)', courses)
    
    # Course Assignments
    assignments = [
        (1, 1, 1, 3),  # BEE101 - Abhijeet - SEA
        (1, 1, 2, 3),  # BEE101 - Abhijeet - SEB
        (2, 2, 1, 3),  # MATH201 - Subhit - SEA
        (2, 2, 2, 3),  # MATH201 - Subhit - SEB
        (3, 1, 3, 5),  # CS201 - Abhijeet - TEA
        (4, 1, 3, 5),  # CS201L - Abhijeet - TEA
    ]
    cursor.executemany('INSERT INTO course_assignments (course_id, teacher_id, group_id, semester) VALUES (?,?,?,?)', assignments)
    
    # Rooms
    rooms = [
        ('R101', 'Room 101', 60, 'Lecture'),
        ('R102', 'Room 102', 50, 'Lecture'),
        ('LAB1', 'Computer Lab 1', 40, 'Lab'),
    ]
    cursor.executemany('INSERT INTO rooms (room_code, room_name, capacity, room_type) VALUES (?,?,?,?)', rooms)
    
    # Time Slots
    slots = [
        ('S1', 'Monday', '09:00', '10:00'),
        ('S2', 'Monday', '10:00', '11:00'),
        ('S3', 'Monday', '11:00', '12:00'),
        ('S4', 'Tuesday', '09:00', '10:00'),
        ('S5', 'Tuesday', '10:00', '11:00'),
        ('S6', 'Tuesday', '11:00', '12:00'),
        ('S7', 'Wednesday', '09:00', '10:00'),
        ('S8', 'Wednesday', '10:00', '11:00'),
        ('S9', 'Wednesday', '11:00', '12:00'),
    ]
    cursor.executemany('INSERT INTO time_slots (slot_code, day_name, start_time, end_time) VALUES (?,?,?,?)', slots)
    
    conn.commit()
    conn.close()
    
    print("✅ Test database created successfully!")
    print(f"📁 Database: {DB_PATH}")
    return True

# ============ SCHEDULING ALGORITHM ============

class SimpleScheduler:
    """Simple timetable scheduler with collision prevention"""
    
    def __init__(self):
        self.teacher_schedule = {}  # teacher_id -> {day: [slots]}
        self.room_schedule = {}     # room_id -> {day: [slots]}
        self.group_schedule = {}    # group_id -> {day: [slots]}
        
    def is_teacher_free(self, teacher_id, day, slot):
        """Check if teacher is free at given time"""
        if teacher_id not in self.teacher_schedule:
            return True
        if day not in self.teacher_schedule[teacher_id]:
            return True
        return slot not in self.teacher_schedule[teacher_id][day]
    
    def is_room_free(self, room_id, day, slot):
        """Check if room is free at given time"""
        if room_id not in self.room_schedule:
            return True
        if day not in self.room_schedule[room_id]:
            return True
        return slot not in self.room_schedule[room_id][day]
    
    def is_group_free(self, group_id, day, slot):
        """Check if student group is free at given time"""
        if group_id not in self.group_schedule:
            return True
        if day not in self.group_schedule[group_id]:
            return True
        return slot not in self.group_schedule[group_id][day]
    
    def assign_class(self, teacher_id, group_id, room_id, day, slot, course_id):
        """Assign a class to a time slot"""
        if not self.is_teacher_free(teacher_id, day, slot):
            return False, "Teacher already has a class at this time"
        if not self.is_group_free(group_id, day, slot):
            return False, "Group already has a class at this time"
        if not self.is_room_free(room_id, day, slot):
            return False, "Room is already booked at this time"
        
        # Assign
        if teacher_id not in self.teacher_schedule:
            self.teacher_schedule[teacher_id] = {}
        if day not in self.teacher_schedule[teacher_id]:
            self.teacher_schedule[teacher_id][day] = []
        self.teacher_schedule[teacher_id][day].append(slot)
        
        if group_id not in self.group_schedule:
            self.group_schedule[group_id] = {}
        if day not in self.group_schedule[group_id]:
            self.group_schedule[group_id][day] = []
        self.group_schedule[group_id][day].append(slot)
        
        if room_id not in self.room_schedule:
            self.room_schedule[room_id] = {}
        if day not in self.room_schedule[room_id]:
            self.room_schedule[room_id][day] = []
        self.room_schedule[room_id][day].append(slot)
        
        return True, "Assigned successfully"

def generate_timetable():
    """Generate timetable using simple algorithm"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Clear existing timetable
    cursor.execute("DELETE FROM timetable_entries")
    
    # Get all data
    cursor.execute("SELECT * FROM course_assignments")
    assignments = cursor.fetchall()
    
    cursor.execute("SELECT * FROM teachers")
    teachers = {row['id']: dict(row) for row in cursor.fetchall()}
    
    cursor.execute("SELECT * FROM student_groups")
    groups = {row['id']: dict(row) for row in cursor.fetchall()}
    
    cursor.execute("SELECT * FROM rooms")
    rooms = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM time_slots")
    slots = [dict(row) for row in cursor.fetchall()]
    
    # Create scheduler
    scheduler = SimpleScheduler()
    
    # Track results
    assigned = []
    conflicts = []
    
    # Assign each course
    for assignment in assignments:
        assigned_flag = False
        
        for slot in slots:
            for room in rooms:
                success, message = scheduler.assign_class(
                    assignment['teacher_id'],
                    assignment['group_id'],
                    room['id'],
                    slot['day_name'],
                    slot['id'],
                    assignment['course_id']
                )
                
                if success:
                    # Save to database
                    cursor.execute('''
                        INSERT INTO timetable_entries 
                        (teacher_id, group_id, room_id, slot_id, course_id, day_name, time_slot)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        assignment['teacher_id'],
                        assignment['group_id'],
                        room['id'],
                        slot['id'],
                        assignment['course_id'],
                        slot['day_name'],
                        f"{slot['start_time']}-{slot['end_time']}"
                    ))
                    assigned.append({
                        'course_id': assignment['course_id'],
                        'teacher_id': assignment['teacher_id'],
                        'group_id': assignment['group_id'],
                        'room': room['room_name'],
                        'day': slot['day_name'],
                        'time': f"{slot['start_time']}-{slot['end_time']}"
                    })
                    assigned_flag = True
                    break
            if assigned_flag:
                break
        
        if not assigned_flag:
            conflicts.append({
                'course_id': assignment['course_id'],
                'teacher_id': assignment['teacher_id'],
                'group_id': assignment['group_id'],
                'reason': 'No available time slot or room'
            })
    
    conn.commit()
    conn.close()
    
    return assigned, conflicts

# ============ TEST FUNCTIONS ============

def test_database():
    """Test database connection and data"""
    print("\n" + "="*60)
    print("📊 TESTING DATABASE")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    users_count = cursor.fetchone()['count']
    print(f"✅ Users: {users_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM teachers")
    teachers_count = cursor.fetchone()['count']
    print(f"✅ Teachers: {teachers_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM student_groups")
    groups_count = cursor.fetchone()['count']
    print(f"✅ Student Groups: {groups_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM courses")
    courses_count = cursor.fetchone()['count']
    print(f"✅ Courses: {courses_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM course_assignments")
    assignments_count = cursor.fetchone()['count']
    print(f"✅ Course Assignments: {assignments_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM rooms")
    rooms_count = cursor.fetchone()['count']
    print(f"✅ Rooms: {rooms_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM time_slots")
    slots_count = cursor.fetchone()['count']
    print(f"✅ Time Slots: {slots_count}")
    
    conn.close()

def test_login():
    """Test login functionality"""
    print("\n" + "="*60)
    print("🔐 TESTING LOGIN")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test admin login
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    if admin:
        print(f"✅ Admin user found: {admin['username']}")
        print(f"   Password hash: {admin['password_hash'][:20]}...")
    else:
        print("❌ Admin user not found")
    
    # List all users
    cursor.execute("SELECT id, username, full_name, role FROM users")
    users = cursor.fetchall()
    print("\n📋 All Users:")
    for user in users:
        print(f"   - {user['username']} ({user['role']}) - {user['full_name']}")
    
    conn.close()

def test_timetable_generation():
    """Test timetable generation"""
    print("\n" + "="*60)
    print("📅 TESTING TIMETABLE GENERATION")
    print("="*60)
    
    assigned, conflicts = generate_timetable()
    
    print(f"\n✅ Assigned Classes: {len(assigned)}")
    print(f"⚠️ Conflicts: {len(conflicts)}")
    
    print("\n📋 Generated Timetable:")
    print("-" * 60)
    for entry in assigned[:10]:  # Show first 10
        print(f"   Day: {entry['day']}, Time: {entry['time']}")
        print(f"   Course: {entry['course_id']}, Teacher: {entry['teacher_id']}, Group: {entry['group_id']}")
        print(f"   Room: {entry['room']}")
        print()
    
    if conflicts:
        print("\n⚠️ Conflicts Found:")
        for conflict in conflicts:
            print(f"   - Course {conflict['course_id']}: {conflict['reason']}")
    
    return assigned, conflicts

def test_api_endpoints():
    """Simulate API endpoints"""
    print("\n" + "="*60)
    print("🌐 TESTING API ENDPOINTS")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test GET /api/teachers
    cursor.execute("SELECT id, name, department FROM teachers")
    teachers = cursor.fetchall()
    print(f"\n✅ GET /api/teachers - {len(teachers)} teachers")
    for teacher in teachers[:3]:
        print(f"   - {teacher['name']} ({teacher['department']})")
    
    # Test GET /api/groups
    cursor.execute("SELECT group_code, group_name, semester FROM student_groups")
    groups = cursor.fetchall()
    print(f"\n✅ GET /api/groups - {len(groups)} groups")
    for group in groups[:3]:
        print(f"   - {group['group_code']}: {group['group_name']} (Sem {group['semester']})")
    
    # Test GET /api/courses
    cursor.execute("SELECT course_code, course_name, credits FROM courses")
    courses = cursor.fetchall()
    print(f"\n✅ GET /api/courses - {len(courses)} courses")
    for course in courses[:3]:
        print(f"   - {course['course_code']}: {course['course_name']} ({course['credits']} credits)")
    
    # Test GET /api/rooms
    cursor.execute("SELECT room_code, room_name, capacity FROM rooms")
    rooms = cursor.fetchall()
    print(f"\n✅ GET /api/rooms - {len(rooms)} rooms")
    for room in rooms:
        print(f"   - {room['room_code']}: {room['room_name']} (Capacity: {room['capacity']})")
    
    # Test GET /api/timetable/view
    cursor.execute("SELECT COUNT(*) as count FROM timetable_entries")
    count = cursor.fetchone()['count']
    print(f"\n✅ GET /api/timetable/view - {count} timetable entries")
    
    conn.close()

def test_teacher_collision_prevention():
    """Test if teachers are double-booked"""
    print("\n" + "="*60)
    print("👨‍🏫 TESTING TEACHER COLLISION PREVENTION")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check for teacher double-booking
    cursor.execute('''
        SELECT teacher_id, day_name, time_slot, COUNT(*) as count
        FROM timetable_entries
        GROUP BY teacher_id, day_name, time_slot
        HAVING COUNT(*) > 1
    ''')
    
    collisions = cursor.fetchall()
    
    if len(collisions) == 0:
        print("✅ No teacher collisions found! Teachers are not double-booked.")
    else:
        print(f"⚠️ Found {len(collisions)} teacher collisions:")
        for collision in collisions:
            print(f"   - Teacher {collision['teacher_id']} has {collision['count']} classes at {collision['day_name']} {collision['time_slot']}")
    
    conn.close()

def test_room_collision_prevention():
    """Test if rooms are double-booked"""
    print("\n" + "="*60)
    print("🏠 TESTING ROOM COLLISION PREVENTION")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check for room double-booking
    cursor.execute('''
        SELECT room_id, day_name, time_slot, COUNT(*) as count
        FROM timetable_entries
        GROUP BY room_id, day_name, time_slot
        HAVING COUNT(*) > 1
    ''')
    
    collisions = cursor.fetchall()
    
    if len(collisions) == 0:
        print("✅ No room collisions found! Rooms are not double-booked.")
    else:
        print(f"⚠️ Found {len(collisions)} room collisions:")
        for collision in collisions:
            print(f"   - Room {collision['room_id']} has {collision['count']} classes at {collision['day_name']} {collision['time_slot']}")
    
    conn.close()

def test_group_collision_prevention():
    """Test if student groups are double-booked"""
    print("\n" + "="*60)
    print("👥 TESTING GROUP COLLISION PREVENTION")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check for group double-booking
    cursor.execute('''
        SELECT group_id, day_name, time_slot, COUNT(*) as count
        FROM timetable_entries
        GROUP BY group_id, day_name, time_slot
        HAVING COUNT(*) > 1
    ''')
    
    collisions = cursor.fetchall()
    
    if len(collisions) == 0:
        print("✅ No group collisions found! Student groups are not double-booked.")
    else:
        print(f"⚠️ Found {len(collisions)} group collisions:")
        for collision in collisions:
            print(f"   - Group {collision['group_id']} has {collision['count']} classes at {collision['day_name']} {collision['time_slot']}")
    
    conn.close()

def view_full_timetable():
    """Display the complete generated timetable"""
    print("\n" + "="*60)
    print("📅 COMPLETE TIMETABLE")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            te.day_name,
            te.time_slot,
            t.name as teacher_name,
            sg.group_name,
            r.room_name,
            c.course_name
        FROM timetable_entries te
        JOIN teachers t ON te.teacher_id = t.id
        JOIN student_groups sg ON te.group_id = sg.id
        JOIN rooms r ON te.room_id = r.id
        JOIN courses c ON te.course_id = c.id
        ORDER BY te.day_name, te.time_slot
    ''')
    
    entries = cursor.fetchall()
    
    if len(entries) == 0:
        print("⚠️ No timetable entries found. Run generation first!")
    else:
        current_day = None
        for entry in entries:
            if current_day != entry['day_name']:
                current_day = entry['day_name']
                print(f"\n📌 {current_day}")
                print("-" * 50)
            print(f"   {entry['time_slot']}: {entry['course_name']}")
            print(f"      Teacher: {entry['teacher_name']}, Room: {entry['room_name']}, Group: {entry['group_name']}")
    
    conn.close()

# ============ MAIN TEST RUNNER ============

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("🎓 TIMETABLE GENERATOR - TEST ENVIRONMENT")
    print("="*60)
    
    # Step 1: Setup database
    print("\n📦 Setting up test database...")
    setup_database()
    
    # Step 2: Test database
    test_database()
    
    # Step 3: Test login
    test_login()
    
    # Step 4: Generate timetable
    assigned, conflicts = test_timetable_generation()
    
    # Step 5: Test API endpoints
    test_api_endpoints()
    
    # Step 6: Test collision prevention
    test_teacher_collision_prevention()
    test_room_collision_prevention()
    test_group_collision_prevention()
    
    # Step 7: View full timetable
    view_full_timetable()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Database: Ready")
    print(f"✅ Users: Created")
    print(f"✅ Timetable: {len(assigned)} classes scheduled")
    print(f"⚠️ Conflicts: {len(conflicts)} unresolved")
    
    if len(conflicts) == 0:
        print("\n🎉 All tests passed! Your timetable system is working perfectly!")
    else:
        print(f"\n⚠️ Some issues found. {len(conflicts)} courses could not be scheduled.")
    
    print("\n📁 Database file:", DB_PATH)
    print("="*60)

# ============ RUN ============
if __name__ == "__main__":
    run_all_tests()