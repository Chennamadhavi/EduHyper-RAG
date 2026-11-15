"""
Course management and student enrollment API router.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import (
    get_current_user,
    get_current_teacher,
)
from backend.app.schemas.course import (
    CourseCreateRequest,
    CourseResponse,
    TeacherEnrollStudentRequest,
    EnrolledStudentResponse,
)
from src.database.models import (
    create_course,
    get_course_by_id,
    get_courses_by_teacher,
    get_all_courses,
    enroll_student_in_course,
    get_student_enrolled_courses,
    get_documents_by_course,
)
from src.database.db import get_db_connection


router = APIRouter()


def _enrich_course(course: Dict[str, Any], current_user_id: Optional[int] = None) -> CourseResponse:
    """Helper to add document and student counts to course record."""
    course_id = course["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Document count
        cursor.execute("SELECT COUNT(*) FROM documents WHERE course_id = ?", (course_id,))
        doc_count = cursor.fetchone()[0]

        # Student count
        cursor.execute("SELECT COUNT(*) FROM course_enrollments WHERE course_id = ?", (course_id,))
        student_count = cursor.fetchone()[0]

        # Is current user enrolled
        is_enrolled = False
        if current_user_id:
            cursor.execute(
                "SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?",
                (course_id, current_user_id),
            )
            is_enrolled = bool(cursor.fetchone())

        return CourseResponse(
            id=course["id"],
            course_code=course["course_code"],
            title=course["title"],
            description=course.get("description") or "",
            teacher_id=course["teacher_id"],
            teacher_name=course.get("teacher_name"),
            document_count=doc_count,
            student_count=student_count,
            created_at=str(course.get("created_at", "")),
            is_enrolled=is_enrolled,
        )
    finally:
        conn.close()


@router.get("", response_model=List[CourseResponse], summary="List courses")
async def list_courses(
    all_courses: bool = Query(default=False, alias="all", description="Return full course catalog"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns courses scoped to the user role:
    - Instructors see their created courses (or all catalog courses if all=true).
    - Students see their enrolled courses (or all catalog courses if all=true).
    """
    user_id = current_user["id"]
    user_role = current_user["role"]

    if all_courses:
        courses = get_all_courses()
    elif user_role == "teacher":
        courses = get_courses_by_teacher(user_id)
    else:
        courses = get_student_enrolled_courses(user_id)

    return [_enrich_course(c, current_user_id=user_id) for c in courses]


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, summary="Create course")
async def create_new_course(
    payload: CourseCreateRequest,
    current_teacher: Dict[str, Any] = Depends(get_current_teacher),
):
    """
    Creates a new course record owned by the authenticated teacher.
    """
    try:
        new_course = create_course(
            course_code=payload.course_code,
            title=payload.title,
            description=payload.description or "",
            teacher_id=current_teacher["id"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _enrich_course(new_course, current_user_id=current_teacher["id"])


@router.get("/{course_id}", response_model=CourseResponse, summary="Get course details")
async def get_course_detail(
    course_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Fetches detailed metadata for a specific course.
    """
    course = get_course_by_id(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} was not found.",
        )
    return _enrich_course(course, current_user_id=current_user["id"])


@router.post("/{course_id}/enroll", summary="Enroll in course")
async def enroll_course(
    course_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Enrolls the current student or user into a course.
    """
    course = get_course_by_id(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} does not exist.",
        )

    enroll_student_in_course(course_id=course_id, student_id=current_user["id"])
    return {
        "success": True,
        "message": f"Successfully enrolled in {course['course_code']} - {course['title']}.",
        "course_id": course_id,
    }


@router.get("/{course_id}/students", response_model=List[EnrolledStudentResponse], summary="List enrolled students in course")
async def list_course_students(
    course_id: int,
    current_teacher: Dict[str, Any] = Depends(get_current_teacher),
):
    """
    Lists enrolled students for an instructor's course.
    """
    course = get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    if course["teacher_id"] != current_teacher["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to view rosters for this course.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT u.id, u.username, u.email, ce.enrolled_at
            FROM course_enrollments ce
            JOIN users u ON ce.student_id = u.id
            WHERE ce.course_id = ?
            ORDER BY ce.enrolled_at DESC
            """,
            (course_id,),
        )
        rows = cursor.fetchall()
        return [
            EnrolledStudentResponse(
                id=r["id"],
                username=r["username"],
                email=r["email"],
                enrolled_at=str(r["enrolled_at"]) if r["enrolled_at"] else None,
            )
            for r in rows
        ]
    finally:
        conn.close()


@router.post("/{course_id}/students", response_model=EnrolledStudentResponse, summary="Enroll student into course by teacher")
async def enroll_student_by_teacher(
    course_id: int,
    payload: TeacherEnrollStudentRequest,
    current_teacher: Dict[str, Any] = Depends(get_current_teacher),
):
    """
    Enrolls a student into the course by the instructor using student username or email.
    """
    course = get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    if course["teacher_id"] != current_teacher["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to manage enrollments for this course.")

    from backend.app.api.auth import find_user_by_username_or_email
    target_user = find_user_by_username_or_email(payload.username_or_email)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail=f"User '{payload.username_or_email}' not found.",
        )

    if target_user["role"] != "student":
        raise HTTPException(
            status_code=400,
            detail=f"User '{target_user['username']}' is a {target_user['role']}, not a student.",
        )

    enroll_student_in_course(course_id=course_id, student_id=target_user["id"])
    return EnrolledStudentResponse(
        id=target_user["id"],
        username=target_user["username"],
        email=target_user["email"],
    )

