"""
Pydantic validation schemas for course management and student enrollments.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CourseCreateRequest(BaseModel):
    """Payload for creating a new course by an instructor."""
    course_code: str = Field(..., min_length=2, max_length=20, description="Unique course code (e.g. BIO101)")
    title: str = Field(..., min_length=3, max_length=150, description="Human-readable course title")
    description: Optional[str] = Field(default="", max_length=500, description="Course summary or syllabus overview")

    @field_validator("course_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Course code cannot be empty.")
        return cleaned

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Course title cannot be empty.")
        return cleaned


class CourseResponse(BaseModel):
    """Detailed course representation."""
    id: int
    course_code: str
    title: str
    description: Optional[str] = ""
    teacher_id: int
    teacher_name: Optional[str] = None
    document_count: Optional[int] = 0
    student_count: Optional[int] = 0
    created_at: Optional[str] = None
    is_enrolled: Optional[bool] = False


class CourseEnrollRequest(BaseModel):
    """Payload for enrolling in a course."""
    course_id: int = Field(..., description="Target course ID")


class TeacherEnrollStudentRequest(BaseModel):
    """Payload for teacher enrolling a student by username or email."""
    username_or_email: str = Field(..., min_length=2, description="Student username or email")


class EnrolledStudentResponse(BaseModel):
    """Information about an enrolled student."""
    id: int
    username: str
    email: str
    enrolled_at: Optional[str] = None
