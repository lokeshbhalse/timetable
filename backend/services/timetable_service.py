# backend/services/timetable_service.py
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from backend.legacy.Bipartite_Matching_Assignment import create_timetable_scheduler
import json
import datetime

class TimetableService:
    def __init__(self):
        self.scheduler = None
    
    def get_scheduler(self):
        if self.scheduler is None:
            self.scheduler = create_timetable_scheduler()
        return self.scheduler
    
    def generate_timetable(self, semester=None, department=None, priority="lab"):
        scheduler = self.get_scheduler()
        
        # Filter courses if needed
        if semester or department:
            filtered_courses = []
            for course in scheduler.courses:
                group = scheduler.student_groups.get(course.group_id)
                if group:
                    if semester and group.semester != semester:
                        continue
                    if department and group.department != department:
                        continue
                filtered_courses.append(course)
            scheduler.courses = filtered_courses
        
        # Generate
        result = scheduler.generate_timetable(priority)
        
        # Save to database
        self._save_to_db(scheduler, result)
        
        return result
    
    def _save_to_db(self, scheduler, result):
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Clear existing entries for current year
            year = str(datetime.datetime.now().year)
            cursor.execute("DELETE FROM timetable_entries WHERE academic_year = ?", (year,))
            
            # Save new assignments
            for assignment in result.get('assignments', []):
                try:
                    # Convert string IDs to integers
                    course_id = int(assignment['course_id']) if str(assignment['course_id']).isdigit() else 1
                    teacher_id = int(assignment['teacher_id']) if str(assignment['teacher_id']).isdigit() else 1
                    group_id = int(assignment['group_id']) if str(assignment['group_id']).isdigit() else 1
                    room_id = int(assignment['room_id']) if str(assignment['room_id']).isdigit() else 1
                    slot_id = int(assignment['slot_id']) if str(assignment['slot_id']).isdigit() else 1
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO timetable_entries 
                        (course_assignment_id, teacher_id, group_id, room_id, slot_id, semester, academic_year, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        course_id, teacher_id, group_id, room_id, slot_id,
                        2024, year, 'scheduled'
                    ))
                except Exception as e:
                    print(f"Error saving assignment: {e}")
            
            conn.commit()
    
    def get_timetable(self, group_id=None, teacher_id=None, room_id=None):
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
                SELECT te.*, ts.day_name, ts.start_time, ts.end_time, ts.slot_name,
                       c.course_name, c.course_code,
                       t.name as teacher_name,
                       sg.name as group_name,
                       r.room_name
                FROM timetable_entries te
                JOIN time_slots ts ON te.slot_id = ts.id
                JOIN course_assignments ca ON te.course_assignment_id = ca.id
                JOIN courses c ON ca.course_id = c.id
                JOIN teachers t ON te.teacher_id = t.id
                JOIN student_groups sg ON te.group_id = sg.id
                JOIN rooms r ON te.room_id = r.id
                WHERE 1=1
            """
            params = []
            if group_id:
                query += " AND te.group_id = ?"
                params.append(group_id)
            if teacher_id:
                query += " AND te.teacher_id = ?"
                params.append(teacher_id)
            if room_id:
                query += " AND te.room_id = ?"
                params.append(room_id)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_group_schedule(self, group_id):
        return self.get_timetable(group_id=group_id)

# Create singleton instance
timetable_service = TimetableService()