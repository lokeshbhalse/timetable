# backend/db_queries.py - Common database queries
from database import get_db
from typing import Dict, List, Optional, Any
from datetime import datetime

class DBQueries:
    """Common database query methods"""
    
    @staticmethod
    def get_teacher_by_id(teacher_id: int) -> Optional[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teachers WHERE id = ? AND is_active = 1", (teacher_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_teacher_by_code(teacher_code: str) -> Optional[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teachers WHERE teacher_code = ? AND is_active = 1", (teacher_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_all_teachers(department: str = None) -> List[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            if department:
                cursor.execute("SELECT * FROM teachers WHERE department = ? AND is_active = 1", (department,))
            else:
                cursor.execute("SELECT * FROM teachers WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_group_by_id(group_id: int) -> Optional[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM student_groups WHERE id = ? AND is_active = 1", (group_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_all_groups(semester: int = None, department: str = None) -> List[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM student_groups WHERE is_active = 1"
            params = []
            if semester:
                query += " AND semester = ?"
                params.append(semester)
            if department:
                query += " AND department = ?"
                params.append(department)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_room_by_id(room_id: int) -> Optional[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rooms WHERE id = ? AND is_active = 1", (room_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_all_rooms(room_type: str = None) -> List[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            if room_type:
                cursor.execute("SELECT * FROM rooms WHERE room_type = ? AND is_active = 1", (room_type,))
            else:
                cursor.execute("SELECT * FROM rooms WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_course_by_id(course_id: int) -> Optional[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_course_assignments(teacher_id: int = None, group_id: int = None, semester: int = None) -> List[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT ca.*, c.course_name, c.course_code, t.name as teacher_name, sg.name as group_name
                FROM course_assignments ca
                JOIN courses c ON ca.course_id = c.id
                JOIN teachers t ON ca.teacher_id = t.id
                JOIN student_groups sg ON ca.group_id = sg.id
                WHERE 1=1
            '''
            params = []
            if teacher_id:
                query += " AND ca.teacher_id = ?"
                params.append(teacher_id)
            if group_id:
                query += " AND ca.group_id = ?"
                params.append(group_id)
            if semester:
                query += " AND ca.semester = ?"
                params.append(semester)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_available_slots_for_teacher(teacher_id: int, day_of_week: int = None) -> List[Dict]:
        """Get time slots where teacher is available"""
        with get_db() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT ts.* FROM time_slots ts
                WHERE ts.is_active = 1 AND ts.is_break = 0
                AND NOT EXISTS (
                    SELECT 1 FROM teacher_unavailability tu
                    WHERE tu.teacher_id = ? AND tu.day_of_week = ts.day_of_week 
                    AND tu.slot_id = ts.id
                )
            '''
            params = [teacher_id]
            if day_of_week is not None:
                query += " AND ts.day_of_week = ?"
                params.append(day_of_week)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_available_rooms_for_slot(slot_id: int, required_capacity: int = 0, is_lab: bool = False) -> List[Dict]:
        """Get available rooms for a given time slot"""
        with get_db() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT r.* FROM rooms r
                WHERE r.is_active = 1
                AND r.capacity >= ?
                AND NOT EXISTS (
                    SELECT 1 FROM room_unavailability ru
                    WHERE ru.room_id = r.id AND ru.slot_id = ?
                )
            '''
            params = [required_capacity or 0, slot_id]
            
            if is_lab:
                query += " AND r.is_lab = 1"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_slots_by_day(day_of_week: int) -> List[Dict]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM time_slots 
                WHERE day_of_week = ? AND is_active = 1 AND is_break = 0
                ORDER BY start_time
            ''', (day_of_week,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_teacher_weekly_schedule(teacher_id: int, week_number: int = 1, academic_year: str = None) -> Dict:
        """Get teacher's weekly schedule organized by day"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            if not academic_year:
                academic_year = str(datetime.now().year)
            
            cursor.execute('''
                SELECT te.*, ts.day_of_week, ts.day_name, ts.start_time, ts.end_time, ts.slot_name,
                       c.course_name, c.course_code, sg.group_name, r.room_name
                FROM timetable_entries te
                JOIN time_slots ts ON te.slot_id = ts.id
                JOIN course_assignments ca ON te.course_assignment_id = ca.id
                JOIN courses c ON ca.course_id = c.id
                JOIN student_groups sg ON te.group_id = sg.id
                JOIN rooms r ON te.room_id = r.id
                WHERE te.teacher_id = ? AND te.week_number = ? AND te.academic_year = ?
                ORDER BY ts.day_of_week, ts.start_time
            ''', (teacher_id, week_number, academic_year))
            
            schedule = {i: [] for i in range(7)}  # 0-6 days
            for row in cursor.fetchall():
                schedule[row['day_of_week']].append(dict(row))
            
            return schedule
    
    @staticmethod
    def log_conflict(conflict_type: str, severity: str, description: str, 
                     teacher_id: int = None, group_id: int = None, 
                     room_id: int = None, slot_id: int = None) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conflict_log (conflict_type, severity, teacher_id, group_id, room_id, slot_id, conflict_description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (conflict_type, severity, teacher_id, group_id, room_id, slot_id, description))
            return cursor.lastrowid

# Initialize queries
db_queries = DBQueries()