"""
AI Tutor API router for interactive, grounded question answering and personal QA history.
Integrates Phase 4 (Hybrid Retrieval), Phase 5 (LangGraph Agent Verification),
Phase 6 (Grounded Answer Generation), Phase 7 (Hallucination Detection),
and Phase 8 (Source Explainability).
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_current_user
from backend.app.schemas.tutor import (
    TutorQueryRequest,
    TutorQueryResponse,
    QAHistoryItem,
)
from src.agents.explanation_agent import EduExplainabilityEngine
from src.agents.verification_graph import run_agentic_verification
from src.database.models import (
    get_document_by_doc_id,
    get_student_qa_history,
    record_qa_history,
)
from src.evaluation.hallucination_checker import HallucinationChecker
from src.generation.answer_generator import EducationalAnswerGenerator
from src.utils.logger import get_logger

logger = get_logger("tutor_api")
router = APIRouter()

DEFAULT_SAMPLE_QUESTIONS = [
    "How does water photolysis work in Photosystem II to produce oxygen?",
    "What is the role of Rubisco in the Calvin cycle?",
    "How do C4 plants suppress photorespiration compared to C3 plants?",
    "How does electron transport in the thylakoid membrane generate an electrochemical gradient for ATP synthesis?",
    "What are the major structural differences between chlorophyll a and chlorophyll b?",
]


@router.get("/sample-questions", response_model=List[str], summary="Get sample educational questions")
async def get_sample_questions():
    """Returns curated educational questions for demonstration and quick testing."""
    return DEFAULT_SAMPLE_QUESTIONS


@router.post("/query", response_model=TutorQueryResponse, summary="Ask AI Tutor with Agentic Verification")
async def ask_ai_tutor(
    payload: TutorQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Executes the complete EduHyper-RAG online pipeline:
    1. Verifies document and course scope
    2. Runs Phase 4 & 5: Hybrid Retrieval + LangGraph Verification State Machine
    3. Runs Phase 6: Factually Grounded Answer Generation
    4. Runs Phase 7: Line-by-Line Claim Verification & Hallucination Checking
    5. Runs Phase 8: Explainability & Evidence Graph Generation
    6. Stores the interaction into SQLite qa_history
    """
    # 1. Validate Document Scope
    doc = get_document_by_doc_id(payload.doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{payload.doc_id}' was not found in knowledge base.",
        )

    try:
        # 2. Phase 4 & 5: Agentic Verification Workflow with document filter
        logger.info(
            f"Invoking EduHyper-RAG workflow for user {current_user['username']} on doc {payload.doc_id}"
        )
        verified_state = run_agentic_verification(
            user_query=payload.query,
            max_iterations=payload.max_iterations or 2,
            doc_id=payload.doc_id,
            course_id=payload.course_id,
        )

        # 3. Phase 6: Grounded Answer Generation
        answer_gen = EducationalAnswerGenerator()
        answer_result = answer_gen.generate_answer(verified_state)

        # 4. Phase 7: Hallucination Verification
        checker = HallucinationChecker(min_support_score=payload.min_support_score or 0.7)
        ver_report = checker.verify_answer(
            answer_text=answer_result.get("answer", ""),
            retrieved_chunks=verified_state.get("retrieved_chunks", []),
            retrieved_hyperedges=verified_state.get("retrieved_hyperedges", []),
            retrieved_concepts=verified_state.get("retrieved_concepts", []),
        )

        # 5. Phase 8: Explainability Engine
        exp_engine = EduExplainabilityEngine()
        exp_report = exp_engine.generate_explanation(verified_state, answer_result, ver_report)

        # Extract metrics
        confidence_level = getattr(exp_report, "confidence_level", "Medium")
        support_score = float(getattr(ver_report, "support_score", 1.0))
        decision = getattr(ver_report, "decision", "VERIFIED")
        reasoning = verified_state.get("verification_reasoning", "Evidence verified from knowledge base.")

        # 6. Record interaction in database
        record_qa_history(
            student_id=current_user["id"],
            doc_id=payload.doc_id,
            course_id=payload.course_id,
            user_query=payload.query,
            generated_answer=answer_result.get("answer", ""),
            confidence_level=confidence_level,
            support_score=support_score,
            verification_decision=decision,
        )

        # Format chunk details for frontend display
        chunk_details = []
        for ch in verified_state.get("retrieved_chunks", []):
            chunk_details.append({
                "chunk_id": ch.get("chunk_id", ""),
                "content": ch.get("content", ""),
                "score": ch.get("score", 0.0),
                "source": ch.get("source", ""),
                "page": ch.get("page"),
            })

        concepts = [c.get("name", "") for c in verified_state.get("retrieved_concepts", []) if c.get("name")]

        return TutorQueryResponse(
            query=payload.query,
            answer=answer_result.get("answer", ""),
            confidence_level=confidence_level,
            support_score=round(support_score, 4),
            verification_decision=decision,
            verification_reasoning=reasoning,
            supporting_chunks=answer_result.get("supporting_chunks", []),
            supporting_hyperedges=answer_result.get("supporting_hyperedges", []),
            retrieved_concepts=concepts,
            retrieved_chunk_details=chunk_details,
            hallucination_report=ver_report.model_dump() if hasattr(ver_report, "model_dump") else None,
            explainability_report=exp_report.model_dump() if hasattr(exp_report, "model_dump") else None,
            doc_id=payload.doc_id,
            course_id=payload.course_id,
        )

    except Exception as e:
        logger.exception(f"AI Tutor execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Tutor pipeline error: {str(e)}",
        )


@router.get("/history", response_model=List[QAHistoryItem], summary="Get student personal QA history")
async def get_my_qa_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves student's personal question answering history with verification decisions.
    """
    raw_history = get_student_qa_history(student_id=current_user["id"], limit=50)

    items = []
    for row in raw_history:
        items.append(
            QAHistoryItem(
                id=row["id"],
                student_id=row["student_id"],
                doc_id=row["doc_id"],
                course_id=row["course_id"],
                user_query=row["user_query"],
                generated_answer=row["generated_answer"],
                confidence_level=row.get("confidence_level", "Medium"),
                support_score=float(row.get("support_score") or 0.0),
                verification_decision=row.get("verification_decision", "VERIFIED"),
                filename=row.get("filename"),
                course_code=row.get("course_code"),
                created_at=str(row.get("created_at", "")),
            )
        )
    return items
