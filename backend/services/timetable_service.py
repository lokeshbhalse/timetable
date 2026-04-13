# backend/services/timetable_service.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from backend.legacy.Bipartite_Matching_Assignment import create_timetable_scheduler
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

        result = scheduler.generate_timetable(priority)
        self._save_to_db(scheduler, result)
        return result

    def _save_to_db(self, scheduler, result):
        with get_db() as conn:
            cursor = conn.cursor()
            year = str(datetime.datetime.now().year)

            # ── Clear existing entries ────────────────────────────────────
            try:
                cursor.execute(
                    "DELETE FROM timetable_entries WHERE academic_year = ?", (year,)
                )
            except Exception as e:
                print(f"Warning: Could not delete by academic_year: {e}")
                cursor.execute("DELETE FROM timetable_entries")

            # ── Save new assignments ──────────────────────────────────────
            for assignment in result.get("assignments", []):
                try:
                    def _to_int(val, fallback=1):
                        try:
                            return int(val) if str(val).isdigit() else fallback
                        except (TypeError, ValueError):
                            return fallback

                    course_id  = _to_int(assignment.get("course_id"))
                    teacher_id = _to_int(assignment.get("teacher_id"))
                    group_id   = _to_int(assignment.get("group_id"))
                    room_id    = _to_int(assignment.get("room_id"))
                    slot_id    = _to_int(assignment.get("slot_id"))

                    # FIX: always write into `course_id` — NOT `course_assignment_id`.
                    # The SELECT in get_timetable() does:
                    #   JOIN courses c ON te.course_id = c.id
                    # so the column MUST be course_id or the JOIN returns nothing.
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO timetable_entries
                            (course_id, teacher_id, group_id, room_id, slot_id,
                             semester, academic_year, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (course_id, teacher_id, group_id, room_id, slot_id,
                         2024, year, "scheduled"),
                    )

                except Exception as e:
                    print(f"Error saving assignment {assignment}: {e}")

            conn.commit()

    def get_timetable(self, group_id=None, teacher_id=None, room_id=None):
        with get_db() as conn:
            cursor = conn.cursor()

            query = """
                SELECT te.*,
                       c.course_name, c.course_code,
                       t.name  AS teacher_name,
                       sg.name AS group_name,
                       r.room_name
                FROM timetable_entries te
                JOIN courses        c  ON te.course_id  = c.id
                JOIN teachers       t  ON te.teacher_id = t.id
                JOIN student_groups sg ON te.group_id   = sg.id
                JOIN rooms          r  ON te.room_id    = r.id
                WHERE 1=1
            """
            params = []

            if group_id is not None:
                query += " AND te.group_id = ?"
                params.append(group_id)
            if teacher_id is not None:
                query += " AND te.teacher_id = ?"
                params.append(teacher_id)
            if room_id is not None:
                query += " AND te.room_id = ?"
                params.append(room_id)

            try:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error in get_timetable: {e}")
                return []

    def get_group_schedule(self, group_id):
        return self.get_timetable(group_id=group_id)


# Singleton instance
timetable_service = TimetableService()