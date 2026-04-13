# backend/routes/admin_routes.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pydantic import BaseModel
from backend.database import db
from backend.auth import require_admin, get_current_user
import sqlite3

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ============ MODELS ============
class UserStatusUpdate(BaseModel):
    is_active: int

class TeacherCreate(BaseModel):
    name: str
    email: str
    department: str

class SubjectCreate(BaseModel):
    code: str
    name: str
    branch: str
    year: int
    semester: int  # ADDED: semester field
    teacher_id: int
    teacher2_id: Optional[int] = None

class SectionCreate(BaseModel):
    group_code: str
    group_name: str
    semester: int
    department: str
    student_count: int = 60

# ============ USER MANAGEMENT ============

@router.get("/users")
async def get_all_users(current_user=Depends(require_admin)):
    """Get all registered users (Admin only)"""
    try:
        query = """
            SELECT id, username, email, full_name, role, created_at, is_active 
            FROM users 
            ORDER BY created_at DESC
        """
        users = db.execute_query(query)
        return {"users": users or []}
    except Exception as e:
        print(f"Error getting users: {e}")
        return {"users": []}

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int, 
    request: UserStatusUpdate, 
    current_user=Depends(require_admin)
):
    """Activate or deactivate a user (Admin only)"""
    try:
        # Check if user exists
        check_query = "SELECT id, role FROM users WHERE id = ?"
        user = db.execute_query(check_query, (user_id,))
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Cannot deactivate admin
        if user[0]['role'] == 'admin' and request.is_active == 0:
            raise HTTPException(status_code=403, detail="Cannot deactivate admin user")
        
        query = "UPDATE users SET is_active = ? WHERE id = ?"
        success = db.execute_update(query, (request.is_active, user_id))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update user status")
        
        return {"success": True, "message": "User status updated"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user=Depends(require_admin)):
    """Delete a user (Admin only, cannot delete admin)"""
    try:
        # Check if user exists and is not admin
        check_query = "SELECT id, role FROM users WHERE id = ?"
        user = db.execute_query(check_query, (user_id,))
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user[0]['role'] == 'admin':
            raise HTTPException(status_code=403, detail="Cannot delete admin user")
        
        query = "DELETE FROM users WHERE id = ?"
        success = db.execute_update(query, (user_id,))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete user")
        
        return {"success": True, "message": "User deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ TEACHER MANAGEMENT ============

@router.post("/teachers")
async def add_teacher(teacher: TeacherCreate, current_user=Depends(require_admin)):
    """Add a new teacher (Admin only)"""
    try:
        # Check if teacher already exists
        check_query = "SELECT id FROM teachers WHERE email = ?"
        existing = db.execute_query(check_query, (teacher.email,))
        
        if existing:
            raise HTTPException(status_code=400, detail="Teacher with this email already exists")
        
        query = """
            INSERT INTO teachers (name, email, department) 
            VALUES (?, ?, ?)
        """
        teacher_id = db.execute_insert(query, (teacher.name, teacher.email, teacher.department))
        
        if not teacher_id:
            raise HTTPException(status_code=500, detail="Failed to add teacher")
        
        return {"success": True, "message": f"Teacher {teacher.name} added", "teacher_id": teacher_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding teacher: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teachers")
async def get_all_teachers(current_user=Depends(require_admin)):
    """Get all teachers (Admin only)"""
    try:
        query = "SELECT id, name, email, department, created_at FROM teachers ORDER BY name"
        teachers = db.execute_query(query)
        return {"teachers": teachers or []}
    except Exception as e:
        print(f"Error getting teachers: {e}")
        return {"teachers": []}

@router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: int, current_user=Depends(require_admin)):
    """Delete a teacher (Admin only)"""
    try:
        # Check if teacher exists
        check_query = "SELECT id FROM teachers WHERE id = ?"
        teacher = db.execute_query(check_query, (teacher_id,))
        
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        # Check if teacher has any course assignments
        assignment_query = "SELECT id FROM course_assignments WHERE teacher_id = ? LIMIT 1"
        assignments = db.execute_query(assignment_query, (teacher_id,))
        
        if assignments:
            raise HTTPException(status_code=400, detail="Cannot delete teacher with assigned courses")
        
        query = "DELETE FROM teachers WHERE id = ?"
        success = db.execute_update(query, (teacher_id,))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete teacher")
        
        return {"success": True, "message": "Teacher deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting teacher: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ SUBJECT MANAGEMENT WITH SEMESTER ============

@router.post("/subjects")
async def add_subject(subject: SubjectCreate, current_user=Depends(require_admin)):
    """Add a new subject with semester (Admin only)"""
    try:
        # Check if subject code already exists
        check_query = "SELECT id FROM subjects WHERE code = ?"
        existing = db.execute_query(check_query, (subject.code,))
        
        if existing:
            raise HTTPException(status_code=400, detail="Subject code already exists")
        
        # Check if teacher exists
        teacher_query = "SELECT id FROM teachers WHERE id = ?"
        teacher = db.execute_query(teacher_query, (subject.teacher_id,))
        
        if not teacher:
            raise HTTPException(status_code=400, detail="Primary teacher not found")
        
        # Insert with semester
        query = """
            INSERT INTO subjects (code, name, branch, year, semester, teacher_id, teacher2_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        subject_id = db.execute_insert(query, (
            subject.code, subject.name, subject.branch, subject.year, 
            subject.semester, subject.teacher_id, subject.teacher2_id
        ))
        
        if not subject_id:
            raise HTTPException(status_code=500, detail="Failed to add subject")
        
        return {"success": True, "message": f"Subject {subject.name} added", "subject_id": subject_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SubjectAssign(BaseModel):
    subject_id: int
    teacher_id: int
    section: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None

@router.post("/subjects/assign")
async def assign_subject(
    assignment: SubjectAssign,
    current_user=Depends(require_admin)
):
    """Assign or update the teacher for an existing subject (Admin only)"""
    try:
        subject_query = "SELECT id, teacher_id, teacher2_id FROM subjects WHERE id = ?"
        subject = db.execute_query(subject_query, (assignment.subject_id,))
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        subject = subject[0]
        teacher_query = "SELECT id FROM teachers WHERE id = ?"
        teacher = db.execute_query(teacher_query, (assignment.teacher_id,))
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

        if subject.get('teacher_id') == assignment.teacher_id:
            return {"success": True, "message": "Teacher already assigned as primary teacher."}
        if subject.get('teacher2_id') == assignment.teacher_id:
            return {"success": True, "message": "Teacher already assigned as secondary teacher."}

        if subject.get('teacher_id') is None:
            query = "UPDATE subjects SET teacher_id = ? WHERE id = ?"
            params = (assignment.teacher_id, assignment.subject_id)
            message = "Primary teacher assigned to subject."
        elif subject.get('teacher2_id') is None:
            query = "UPDATE subjects SET teacher2_id = ? WHERE id = ?"
            params = (assignment.teacher_id, assignment.subject_id)
            message = "Secondary teacher assigned to subject."
        else:
            query = "UPDATE subjects SET teacher2_id = ? WHERE id = ?"
            params = (assignment.teacher_id, assignment.subject_id)
            message = "Secondary teacher updated for subject."

        updated = db.execute_update(query, params)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to assign teacher to subject")

        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error assigning subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subjects")
async def get_all_subjects(
    branch: Optional[str] = None, 
    year: Optional[int] = None,
    semester: Optional[int] = None,
    current_user=Depends(require_admin)
):
    """Get all subjects with optional filters (Admin only)"""
    try:
        query = """
            SELECT s.*, 
                   t1.name as teacher1_name, 
                   t2.name as teacher2_name,
                   t1.email as teacher1_email,
                   t2.email as teacher2_email
            FROM subjects s
            LEFT JOIN teachers t1 ON s.teacher_id = t1.id
            LEFT JOIN teachers t2 ON s.teacher2_id = t2.id
            WHERE 1=1
        """
        params = []
        
        if branch:
            query += " AND s.branch = ?"
            params.append(branch)
        
        if year:
            query += " AND s.year = ?"
            params.append(year)
        
        if semester:
            query += " AND s.semester = ?"
            params.append(semester)
        
        query += " ORDER BY s.branch, s.year, s.semester, s.code"
        
        subjects = db.execute_query(query, tuple(params))
        return {"subjects": subjects or []}
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return {"subjects": []}

@router.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: int, current_user=Depends(require_admin)):
    """Delete a subject (Admin only)"""
    try:
        # Check if subject exists
        check_query = "SELECT id FROM subjects WHERE id = ?"
        subject = db.execute_query(check_query, (subject_id,))
        
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Check if subject has any timetable entries
        timetable_query = "SELECT id FROM timetable_entries WHERE course_id = ? LIMIT 1"
        entries = db.execute_query(timetable_query, (subject_id,))
        
        if entries:
            raise HTTPException(status_code=400, detail="Cannot delete subject with existing timetable entries")
        
        query = "DELETE FROM subjects WHERE id = ?"
        success = db.execute_update(query, (subject_id,))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete subject")
        
        return {"success": True, "message": "Subject deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ SECTION MANAGEMENT (Optional) ============

@router.post("/sections")
async def create_section(section: SectionCreate, current_user=Depends(require_admin)):
    """Create a new student section (Optional - Admin only)"""
    try:
        query = """
            INSERT INTO student_groups (group_code, group_name, semester, department, student_count) 
            VALUES (?, ?, ?, ?, ?)
        """
        section_id = db.execute_insert(query, (
            section.group_code, section.group_name, section.semester, 
            section.department, section.student_count
        ))
        
        if not section_id:
            raise HTTPException(status_code=500, detail="Failed to create section")
        
        return {"success": True, "message": f"Section {section.group_name} created", "section_id": section_id}
    except Exception as e:
        print(f"Error creating section: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sections")
async def get_all_sections(current_user=Depends(require_admin)):
    """Get all student sections (Admin only)"""
    try:
        query = "SELECT id, group_code, group_name, semester, department, student_count FROM student_groups ORDER BY semester, department"
        sections = db.execute_query(query)
        return {"sections": sections or []}
    except Exception as e:
        print(f"Error getting sections: {e}")
        return {"sections": []}

# ============ STATISTICS ============

@router.get("/stats")
async def get_admin_stats(current_user=Depends(require_admin)):
    """Get system statistics for admin dashboard"""
    try:
        stats = {}
        
        # Count users by role
        users_query = "SELECT role, COUNT(*) as count FROM users GROUP BY role"
        user_counts = db.execute_query(users_query)
        stats['users'] = {row['role']: row['count'] for row in user_counts} if user_counts else {}
        stats['total_users'] = sum(stats['users'].values())
        
        # Count teachers
        teacher_query = "SELECT COUNT(*) as count FROM teachers"
        teacher_count = db.execute_query(teacher_query)
        stats['teachers'] = teacher_count[0]['count'] if teacher_count else 0
        
        # Count subjects
        subject_query = "SELECT COUNT(*) as count FROM subjects"
        subject_count = db.execute_query(subject_query)
        stats['subjects'] = subject_count[0]['count'] if subject_count else 0
        
        # Count sections
        section_query = "SELECT COUNT(*) as count FROM student_groups"
        section_count = db.execute_query(section_query)
        stats['sections'] = section_count[0]['count'] if section_count else 0
        
        # Count timetable entries
        timetable_query = "SELECT COUNT(*) as count FROM timetable_entries"
        timetable_count = db.execute_query(timetable_query)
        stats['timetable_entries'] = timetable_count[0]['count'] if timetable_count else 0
        
        return {"stats": stats}
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {"stats": {}}