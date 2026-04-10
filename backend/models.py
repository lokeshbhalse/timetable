# backend/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Auth Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # student, teacher, admin

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r'^[0-9]{10}$')
    department: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: str
    student_id: Optional[str] = None
    faculty_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

# Course Models
class CourseBase(BaseModel):
    course_name: str
    no_of_students: int = Field(..., gt=0)
    semester: str
    department: str
    lab: str = Field(..., pattern=r'^[yn]$')
    preference: int = 0
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

# Room Models
class RoomBase(BaseModel):
    room_no: str
    capacity: int = Field(..., gt=0)

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    pass

# Faculty Models
class FacultyBase(BaseModel):
    name: str
    email: EmailStr
    department: str
    phone: Optional[str] = None

class FacultyCreate(FacultyBase):
    password: str = Field(..., min_length=6)

class FacultyResponse(FacultyBase):
    fac_id: int
    
    class Config:
        from_attributes = True

# Slot Models
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

# Timetable Models
class TimetableGenerateRequest(BaseModel):
    semester_filter: Optional[str] = None
    department_filter: Optional[str] = None
    courses: Optional[List[CourseBase]] = None

class TimetableResponse(BaseModel):
    status: str
    timetables: dict
    message: str
    generated_at: datetime = Field(default_factory=datetime.now)

# Response Models
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None