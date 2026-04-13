# backend/models.py - SQLite Compatible Version
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime

# ============ AUTH MODELS ============
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r'^[0-9]{10}$')
    department: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: str = Field(default="student", pattern=r'^(admin|teacher|student)$')
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['admin', 'teacher', 'student']:
            return 'student'
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

# ============ TEACHER MODELS ============
class TeacherCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department: str = Field(..., min_length=2)

class TeacherResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str
    created_at: Optional[str] = None

# ============ SUBJECT MODELS ============
class SubjectCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    branch: str = Field(..., min_length=2)
    year: int = Field(..., ge=1, le=4)
    teacher_id: int
    teacher2_id: Optional[int] = None

class SubjectResponse(BaseModel):
    id: int
    code: str
    name: str
    branch: str
    year: int
    teacher_id: int
    teacher2_id: Optional[int] = None
    teacher1_name: Optional[str] = None
    teacher2_name: Optional[str] = None

# ============ COURSE MODELS ============
class CourseBase(BaseModel):
    course_name: str = Field(..., min_length=2)
    no_of_students: int = Field(..., gt=0)
    semester: str
    department: str
    lab: str = Field(..., pattern=r'^[yn]$')
    preference: int = Field(default=0, ge=0, le=10)
    preferred_room: Optional[str] = None
    preferred_slot: Optional[str] = None
    division: Optional[str] = None
    lab_room: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    
    class Config:
        from_attributes = True

# ============ ROOM MODELS ============
class RoomBase(BaseModel):
    room_no: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: int

# ============ FACULTY MODELS ============
class FacultyBase(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    department: str
    phone: Optional[str] = Field(None, pattern=r'^[0-9]{10}$')

class FacultyCreate(FacultyBase):
    password: str = Field(..., min_length=6)

class FacultyResponse(FacultyBase):
    fac_id: int
    
    class Config:
        from_attributes = True

# ============ SLOT MODELS ============
class SlotBase(BaseModel):
    slot_name: str
    day: str
    time_from: str
    till_time: str

class SlotCreate(SlotBase):
    pass

class SlotResponse(SlotBase):
    slot_id: int
    
    class Config:
        from_attributes = True

# ============ SECTION MODELS ============
class SectionCreate(BaseModel):
    group_code: str = Field(..., min_length=2, max_length=10)
    group_name: str = Field(..., min_length=2)
    semester: int = Field(..., ge=1, le=8)
    department: str
    student_count: int = Field(default=60, ge=1)

class SectionResponse(BaseModel):
    id: int
    group_code: str
    group_name: str
    semester: int
    department: str
    student_count: int

# ============ TIMETABLE MODELS ============
class TimetableGenerateRequest(BaseModel):
    branch: str
    year: int
    section: str
    semester: int = Field(default=1, ge=1, le=8)

class TimetableResponse(BaseModel):
    status: str
    message: str
    assignments: Optional[int] = None
    timetable: Optional[dict] = None
    generated_at: datetime = Field(default_factory=datetime.now)

# ============ USER MANAGEMENT MODELS ============
class UserStatusUpdate(BaseModel):
    is_active: int = Field(default=1, ge=0, le=1)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: int
    created_at: str

# ============ RESPONSE MODELS ============
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# ============ ADMIN STATS MODELS ============
class AdminStatsResponse(BaseModel):
    total_users: int = 0
    total_teachers: int = 0
    total_subjects: int = 0
    total_sections: int = 0
    total_timetable_entries: int = 0
    users_by_role: dict = {}