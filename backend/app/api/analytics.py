"""
Analytics and Learning Progress API Router for EduHyper-RAG.
Provides classroom quality monitoring, hallucination auditing for teachers,
personal learning mastery tracking for students, and Phase 9 benchmark evaluations.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_current_user, require_role
from backend.app.schemas.analytics import (
    BenchmarkResponse,
    BenchmarkRow,
    CourseAnalyticsItem,
    RecentQuestionItem,
    StudentCourseProgressItem,
    StudentProgressResponse,
    TeacherAnalyticsResponse,
)
from src.database.db import get_db_connection
from src.utils.logger import get_logger

logger = get_logger("analytics_api")
router = APIRouter()

# Canonical Phase 9 empirical benchmark dataset
BENCHMARK_ROWS = [
    BenchmarkRow(
        architecture="Vanilla LLM",
        correctness=0.1229,
        faithfulness=1.0000,
        context_recall=0.0000,
        kmr=1.0000,
        her=0.0000,
        latency_ms=0.15,
    ),
    BenchmarkRow(
        architecture="Traditional RAG",
        correctness=0.0894,
        faithfulness=0.9159,
        context_recall=0.9000,
        kmr=0.1000,
        her=0.0841,
        latency_ms=489.87,
    ),
    BenchmarkRow(
        architecture="GraphRAG",
        correctness=0.0898,
        faithfulness=0.9225,
        context_recall=1.0000,
        kmr=0.0000,
        her=0.0775,
        latency_ms=419.66,
    ),
    BenchmarkRow(
        architecture="LightRAG",
        correctness=0.0995,
        faithfulness=0.9266,
        context_recall=1.0000,
        kmr=0.0000,
        her=0.0734,
        latency_ms=409.76,
    ),
    BenchmarkRow(
        architecture="Original Hyper-RAG",
        correctness=0.0995,
        faithfulness=0.9381,
        context_recall=1.0000,
        kmr=0.0000,
        her=0.0619,
        latency_ms=431.17,
    ),
    BenchmarkRow(
        architecture="Proposed Enhanced Hyper-RAG",
        correctness=0.0941,
        faithfulness=0.9488,
        context_recall=1.0000,
        kmr=0.0000,
        her=0.0512,
        latency_ms=515.21,
    ),
]


@router.get(
    "/teacher",
    response_model=TeacherAnalyticsResponse,
    summary="Get teacher classroom analytics and hallucination audit summary",
)
async def get_teacher_analytics(
    current_user: Dict[str, Any] = Depends(require_role("teacher")),
):
    """
    Computes quality metrics across all courses owned by the authenticated instructor:
    - Active courses and processed documents count
    - Student query volume and average factual grounding support score
    - Hallucination flag rate and flagged queries audit list
    - Course-by-course breakdown
    - Verification decisions and confidence distributions
    """
    teacher_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Total Courses
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE teacher_id = ?", (teacher_id,))
        total_courses = cursor.fetchone()["count"]

        # 2. Total Documents
        cursor.execute(
            """
            SELECT COUNT(*) as count FROM documents d
            JOIN courses c ON d.course_id = c.id
            WHERE c.teacher_id = ?
            """,
            (teacher_id,),
        )
        total_documents = cursor.fetchone()["count"]

        # 3. Overall QA Stats across instructor's courses
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_queries,
                AVG(q.support_score) as avg_support_score,
                SUM(CASE WHEN q.verification_decision IN ('REGENERATE', 'REJECT_INSUFFICIENT', 'UNSUPPORTED') THEN 1 ELSE 0 END) as flagged_queries
            FROM qa_history q
            JOIN courses c ON q.course_id = c.id
            WHERE c.teacher_id = ?
            """,
            (teacher_id,),
        )
        qa_stats = cursor.fetchone()
        total_queries = qa_stats["total_queries"] or 0
        avg_support_score = round(float(qa_stats["avg_support_score"] or 0.0), 3)
        flagged_queries = qa_stats["flagged_queries"] or 0
        hallucination_rate = (
            round((flagged_queries / total_queries * 100), 2) if total_queries > 0 else 0.0
        )

        # 4. Decisions Breakdown
        cursor.execute(
            """
            SELECT q.verification_decision, COUNT(*) as count
            FROM qa_history q
            JOIN courses c ON q.course_id = c.id
            WHERE c.teacher_id = ?
            GROUP BY q.verification_decision
            """,
            (teacher_id,),
        )
        decisions_breakdown = {
            row["verification_decision"] or "UNKNOWN": row["count"] for row in cursor.fetchall()
        }

        # 5. Confidence Breakdown
        cursor.execute(
            """
            SELECT q.confidence_level, COUNT(*) as count
            FROM qa_history q
            JOIN courses c ON q.course_id = c.id
            WHERE c.teacher_id = ?
            GROUP BY q.confidence_level
            """,
            (teacher_id,),
        )
        confidence_breakdown = {
            row["confidence_level"] or "UNKNOWN": row["count"] for row in cursor.fetchall()
        }

        # 6. Course-by-course Breakdown
        cursor.execute(
            """
            SELECT 
                c.id as course_id,
                c.course_code,
                c.title,
                COUNT(DISTINCT e.student_id) as enrolled_count,
                COUNT(q.id) as total_queries,
                AVG(q.support_score) as avg_support_score,
                SUM(CASE WHEN q.verification_decision IN ('REGENERATE', 'REJECT_INSUFFICIENT', 'UNSUPPORTED') THEN 1 ELSE 0 END) as flagged_queries
            FROM courses c
            LEFT JOIN course_enrollments e ON c.id = e.course_id
            LEFT JOIN qa_history q ON c.id = q.course_id
            WHERE c.teacher_id = ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """,
            (teacher_id,),
        )
        course_rows = cursor.fetchall()
        courses_breakdown = [
            CourseAnalyticsItem(
                course_id=r["course_id"],
                course_code=r["course_code"],
                title=r["title"],
                total_queries=r["total_queries"] or 0,
                avg_support_score=round(float(r["avg_support_score"] or 0.0), 3),
                flagged_queries=r["flagged_queries"] or 0,
                enrolled_count=r["enrolled_count"] or 0,
            )
            for r in course_rows
        ]

        # 7. Recent Questions
        cursor.execute(
            """
            SELECT 
                q.id,
                q.user_query,
                q.timestamp,
                q.confidence_level,
                q.support_score,
                q.verification_decision,
                u.username as student_name,
                d.filename,
                c.course_code
            FROM qa_history q
            JOIN courses c ON q.course_id = c.id
            JOIN users u ON q.student_id = u.id
            LEFT JOIN documents d ON q.doc_id = d.doc_id
            WHERE c.teacher_id = ?
            ORDER BY q.timestamp DESC
            LIMIT 15
            """,
            (teacher_id,),
        )
        recent_questions = [
            RecentQuestionItem(
                id=r["id"],
                user_query=r["user_query"],
                timestamp=str(r["timestamp"]),
                confidence_level=r["confidence_level"] or "MEDIUM",
                support_score=round(float(r["support_score"] or 0.0), 3),
                verification_decision=r["verification_decision"] or "VERIFIED",
                student_name=r["student_name"],
                filename=r["filename"],
                course_code=r["course_code"],
            )
            for r in cursor.fetchall()
        ]

        # 8. Flagged Questions
        cursor.execute(
            """
            SELECT 
                q.id,
                q.user_query,
                q.timestamp,
                q.confidence_level,
                q.support_score,
                q.verification_decision,
                u.username as student_name,
                d.filename,
                c.course_code
            FROM qa_history q
            JOIN courses c ON q.course_id = c.id
            JOIN users u ON q.student_id = u.id
            LEFT JOIN documents d ON q.doc_id = d.doc_id
            WHERE c.teacher_id = ? AND q.verification_decision IN ('REGENERATE', 'REJECT_INSUFFICIENT', 'UNSUPPORTED')
            ORDER BY q.timestamp DESC
            LIMIT 20
            """,
            (teacher_id,),
        )
        flagged_questions = [
            RecentQuestionItem(
                id=r["id"],
                user_query=r["user_query"],
                timestamp=str(r["timestamp"]),
                confidence_level=r["confidence_level"] or "MEDIUM",
                support_score=round(float(r["support_score"] or 0.0), 3),
                verification_decision=r["verification_decision"] or "REGENERATE",
                student_name=r["student_name"],
                filename=r["filename"],
                course_code=r["course_code"],
            )
            for r in cursor.fetchall()
        ]

        return TeacherAnalyticsResponse(
            total_courses=total_courses,
            total_documents=total_documents,
            total_queries=total_queries,
            avg_support_score=avg_support_score,
            flagged_queries=flagged_queries,
            hallucination_rate_pct=hallucination_rate,
            courses_breakdown=courses_breakdown,
            decisions_breakdown=decisions_breakdown,
            confidence_breakdown=confidence_breakdown,
            recent_questions=recent_questions,
            flagged_questions=flagged_questions,
        )

    finally:
        conn.close()


@router.get(
    "/student",
    response_model=StudentProgressResponse,
    summary="Get student personal learning progress and mastery metrics",
)
async def get_student_progress(
    current_user: Dict[str, Any] = Depends(require_role("student")),
):
    """
    Computes personalized study analytics for the authenticated student:
    - Questions asked and average evidence grounding rate
    - Verified answer percentage
    - Course-by-course query count and grounding mastery
    - Recent learning activity timeline
    """
    student_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Enrolled courses count
        cursor.execute(
            "SELECT COUNT(*) as count FROM course_enrollments WHERE student_id = ?",
            (student_id,),
        )
        enrolled_courses_count = cursor.fetchone()["count"]

        # 2. Overall query stats
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_queries,
                AVG(support_score) as avg_support_score,
                SUM(CASE WHEN verification_decision IN ('VERIFIED', 'ACCEPT') THEN 1 ELSE 0 END) as verified_queries
            FROM qa_history
            WHERE student_id = ?
            """,
            (student_id,),
        )
        stats = cursor.fetchone()
        total_queries = stats["total_queries"] or 0
        avg_support_score = round(float(stats["avg_support_score"] or 0.0), 3)
        verified_queries = stats["verified_queries"] or 0
        verified_rate = (
            round((verified_queries / total_queries * 100), 2) if total_queries > 0 else 0.0
        )

        # 3. Decisions Breakdown
        cursor.execute(
            """
            SELECT verification_decision, COUNT(*) as count
            FROM qa_history
            WHERE student_id = ?
            GROUP BY verification_decision
            """,
            (student_id,),
        )
        decisions_breakdown = {
            row["verification_decision"] or "UNKNOWN": row["count"] for row in cursor.fetchall()
        }

        # 4. Confidence Breakdown
        cursor.execute(
            """
            SELECT confidence_level, COUNT(*) as count
            FROM qa_history
            WHERE student_id = ?
            GROUP BY confidence_level
            """,
            (student_id,),
        )
        confidence_breakdown = {
            row["confidence_level"] or "UNKNOWN": row["count"] for row in cursor.fetchall()
        }

        # 5. Course progress breakdown
        cursor.execute(
            """
            SELECT 
                c.id as course_id,
                c.course_code,
                c.title,
                COUNT(q.id) as queries_count,
                AVG(q.support_score) as avg_support_score
            FROM course_enrollments e
            JOIN courses c ON e.course_id = c.id
            LEFT JOIN qa_history q ON c.id = q.course_id AND q.student_id = e.student_id
            WHERE e.student_id = ?
            GROUP BY c.id
            ORDER BY queries_count DESC
            """,
            (student_id,),
        )
        course_progress = [
            StudentCourseProgressItem(
                course_id=r["course_id"],
                course_code=r["course_code"],
                title=r["title"],
                queries_count=r["queries_count"] or 0,
                avg_support_score=round(float(r["avg_support_score"] or 0.0), 3),
            )
            for r in cursor.fetchall()
        ]

        # 6. Recent Activity
        cursor.execute(
            """
            SELECT 
                q.id,
                q.user_query,
                q.timestamp,
                q.confidence_level,
                q.support_score,
                q.verification_decision,
                d.filename,
                c.course_code
            FROM qa_history q
            LEFT JOIN courses c ON q.course_id = c.id
            LEFT JOIN documents d ON q.doc_id = d.doc_id
            WHERE q.student_id = ?
            ORDER BY q.timestamp DESC
            LIMIT 10
            """,
            (student_id,),
        )
        recent_activity = [
            RecentQuestionItem(
                id=r["id"],
                user_query=r["user_query"],
                timestamp=str(r["timestamp"]),
                confidence_level=r["confidence_level"] or "MEDIUM",
                support_score=round(float(r["support_score"] or 0.0), 3),
                verification_decision=r["verification_decision"] or "VERIFIED",
                student_name=current_user["username"],
                filename=r["filename"],
                course_code=r["course_code"],
            )
            for r in cursor.fetchall()
        ]

        return StudentProgressResponse(
            student_id=student_id,
            student_name=current_user["username"],
            total_queries=total_queries,
            enrolled_courses_count=enrolled_courses_count,
            avg_support_score=avg_support_score,
            verified_rate_pct=verified_rate,
            decisions_breakdown=decisions_breakdown,
            confidence_breakdown=confidence_breakdown,
            course_progress=course_progress,
            recent_activity=recent_activity,
        )

    finally:
        conn.close()


@router.get(
    "/benchmark",
    response_model=BenchmarkResponse,
    summary="Get Phase 9 empirical benchmark evaluation results",
)
async def get_benchmark_results(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns empirical evaluation results comparing Proposed Enhanced Hyper-RAG against
    Vanilla LLM, Traditional RAG, GraphRAG, LightRAG, and Original Hyper-RAG.
    """
    return BenchmarkResponse(
        title="Comparative Evaluation: Retrieval Architectures on Educational QA",
        dataset_size=10,
        rows=BENCHMARK_ROWS,
    )
