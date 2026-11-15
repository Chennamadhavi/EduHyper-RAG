"""
Data Access Layer (CRUD Helper Functions) for EduHyperRAG.
Handles interaction with users, courses, documents, enrollments, and QA logs.
"""

import sqlite3
from typing import Any, Dict, List, Optional
from src.database.db import get_db_connection


# -----------------------------------------------------------------------------
# USER MODELS
# -----------------------------------------------------------------------------

def create_user(username: str, email: str, password_hash: str, role: str) -> Dict[str, Any]:
    """Creates a new user record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username.strip(), email.strip().lower(), password_hash, role.strip().lower()),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"User with username '{username}' or email '{email}' already exists.") from e
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetches user record by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user record by user ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# COURSE MODELS
# -----------------------------------------------------------------------------

def create_course(course_code: str, title: str, description: str, teacher_id: int) -> Dict[str, Any]:
    """Creates a new course record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO courses (course_code, title, description, teacher_id) VALUES (?, ?, ?, ?)",
            (course_code.strip().upper(), title.strip(), description.strip(), teacher_id),
        )
        conn.commit()
        course_id = cursor.lastrowid
        return get_course_by_id(course_id)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Course code '{course_code}' already exists.") from e
    finally:
        conn.close()


def get_course_by_id(course_id: int) -> Optional[Dict[str, Any]]:
    """Fetches course record by course ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_courses_by_teacher(teacher_id: int) -> List[Dict[str, Any]]:
    """Fetches all courses created by a specific teacher."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM courses WHERE teacher_id = ? ORDER BY created_at DESC", (teacher_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_courses() -> List[Dict[str, Any]]:
    """Fetches all courses in the system."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT c.*, u.username as teacher_name 
            FROM courses c 
            JOIN users u ON c.teacher_id = u.id 
            ORDER BY c.created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# DOCUMENT MODELS
# -----------------------------------------------------------------------------

def create_document(
    doc_id: str,
    filename: str,
    file_path: str,
    course_id: int,
    uploaded_by: int,
    status: str = "PROCESSING",
) -> Dict[str, Any]:
    """Creates a new document metadata record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO documents (doc_id, filename, file_path, course_id, uploaded_by, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (doc_id.strip(), filename.strip(), file_path, course_id, uploaded_by, status),
        )
        conn.commit()
        doc_record_id = cursor.lastrowid
        return get_document_by_id(doc_record_id)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Document ID '{doc_id}' already exists.") from e
    finally:
        conn.close()


def update_document_status(
    doc_id: str,
    status: str,
    num_chunks: int = 0,
    num_concepts: int = 0,
    num_hyperedges: int = 0,
) -> None:
    """Updates status and statistics of a processed document."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE documents 
            SET status = ?, num_chunks = ?, num_concepts = ?, num_hyperedges = ?
            WHERE doc_id = ?
            """,
            (status, num_chunks, num_concepts, num_hyperedges, doc_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_document_by_id(doc_record_id: int) -> Optional[Dict[str, Any]]:
    """Fetches document by integer record ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_record_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_document_by_doc_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a document by its unique string doc_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_documents_by_course(course_id: int) -> List[Dict[str, Any]]:
    """Fetches all documents associated with a specific course."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM documents WHERE course_id = ? ORDER BY created_at DESC", (course_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_documents() -> List[Dict[str, Any]]:
    """Fetches all documents across all courses."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# COURSE ENROLLMENT MODELS
# -----------------------------------------------------------------------------

def enroll_student_in_course(course_id: int, student_id: int) -> None:
    """Enrolls a student in a course."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO course_enrollments (course_id, student_id) VALUES (?, ?)",
            (course_id, student_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_student_enrolled_courses(student_id: int) -> List[Dict[str, Any]]:
    """Fetches all courses in which a student is enrolled."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT c.*, u.username as teacher_name
            FROM courses c
            JOIN course_enrollments ce ON c.id = ce.course_id
            JOIN users u ON c.teacher_id = u.id
            WHERE ce.student_id = ?
            ORDER BY ce.enrolled_at DESC
            """,
            (student_id,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_student_accessible_documents(student_id: int) -> List[Dict[str, Any]]:
    """Fetches all ready documents belonging to courses enrolled by student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT d.*, c.title as course_title, c.course_code
            FROM documents d
            JOIN courses c ON d.course_id = c.id
            JOIN course_enrollments ce ON c.id = ce.course_id
            WHERE ce.student_id = ? AND d.status = 'READY'
            ORDER BY d.created_at DESC
            """,
            (student_id,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# QA HISTORY & ANALYTICS MODELS
# -----------------------------------------------------------------------------

def record_qa_history(
    student_id: int,
    doc_id: str,
    course_id: int,
    user_query: str,
    generated_answer: str,
    confidence_level: str,
    support_score: float,
    verification_decision: str,
) -> int:
    """Records a student QA interaction in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO qa_history 
            (student_id, doc_id, course_id, user_query, generated_answer, confidence_level, support_score, verification_decision)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                doc_id,
                course_id,
                user_query,
                generated_answer,
                confidence_level,
                support_score,
                verification_decision,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_student_qa_history(student_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches personal QA history for a specific student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT q.*, d.filename, c.course_code
            FROM qa_history q
            LEFT JOIN documents d ON q.doc_id = d.doc_id
            LEFT JOIN courses c ON q.course_id = c.id
            WHERE q.student_id = ?
            ORDER BY q.timestamp DESC
            LIMIT ?
            """,
            (student_id, limit),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_teacher_analytics_summary(teacher_id: int) -> Dict[str, Any]:
    """Generates analytics summary for courses owned by a teacher."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Total Courses & Documents
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE teacher_id = ?", (teacher_id,))
        total_courses = cursor.fetchone()["count"]

        cursor.execute(
            """
            SELECT COUNT(*) as count FROM documents d
            JOIN courses c ON d.course_id = c.id
            WHERE c.teacher_id = ?
            """,
            (teacher_id,),
        )
        total_documents = cursor.fetchone()["count"]

        # QA Activity Stats
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_queries,
                AVG(q.support_score) as avg_support_score,
                SUM(CASE WHEN q.verification_decision = 'REGENERATE' OR q.verification_decision = 'REJECT_INSUFFICIENT' THEN 1 ELSE 0 END) as flagged_queries
            FROM qa_history q
            JOIN courses c ON q.course_id = c.id
            WHERE c.teacher_id = ?
            """,
            (teacher_id,),
        )
        qa_stats = cursor.fetchone()

        total_queries = qa_stats["total_queries"] or 0
        avg_support_score = round(qa_stats["avg_support_score"] or 0.0, 2)
        flagged_queries = qa_stats["flagged_queries"] or 0
        hallucination_rate = round((flagged_queries / total_queries * 100), 2) if total_queries > 0 else 0.0

        # Recent Questions
        cursor.execute(
            """
            SELECT q.user_query, q.timestamp, q.confidence_level, q.support_score, u.username as student_name, d.filename
            FROM qa_history q
            JOIN courses c ON q.course_id = c.id
            JOIN users u ON q.student_id = u.id
            LEFT JOIN documents d ON q.doc_id = d.doc_id
            WHERE c.teacher_id = ?
            ORDER BY q.timestamp DESC
            LIMIT 10
            """,
            (teacher_id,),
        )
        recent_questions = [dict(r) for r in cursor.fetchall()]

        return {
            "total_courses": total_courses,
            "total_documents": total_documents,
            "total_queries": total_queries,
            "avg_support_score": avg_support_score,
            "flagged_queries": flagged_queries,
            "hallucination_rate_pct": hallucination_rate,
            "recent_questions": recent_questions,
        }
    finally:
        conn.close()
