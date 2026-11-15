"""
Document upload and dynamic ingestion API router.
Reuses existing DocumentProcessingService and Phase 1-4 pipelines.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from backend.app.api.deps import (
    get_current_user,
    get_current_teacher,
)
from backend.app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
)
from src.database.models import (
    get_all_documents,
    get_documents_by_course,
    get_document_by_doc_id,
    get_student_accessible_documents,
    get_course_by_id,
)
from src.services.document_service import DocumentProcessingService
from src.database.db import get_db_connection
from src.utils.logger import get_logger

logger = get_logger("documents_api")
router = APIRouter()


def _enrich_document(doc: Dict[str, Any]) -> DocumentResponse:
    """Helper to attach course title and code if not present in row."""
    course_id = doc.get("course_id")
    course_code = doc.get("course_code")
    course_title = doc.get("course_title")

    if not course_code and course_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT course_code, title FROM courses WHERE id = ?", (course_id,))
            crow = cursor.fetchone()
            if crow:
                course_code = crow["course_code"]
                course_title = crow["title"]
        finally:
            conn.close()

    return DocumentResponse(
        id=doc["id"],
        doc_id=doc["doc_id"],
        filename=doc["filename"],
        course_id=doc["course_id"],
        course_code=course_code,
        course_title=course_title,
        uploaded_by=doc["uploaded_by"],
        status=doc.get("status", "READY"),
        num_chunks=doc.get("num_chunks") or 0,
        num_concepts=doc.get("num_concepts") or 0,
        num_hyperedges=doc.get("num_hyperedges") or 0,
        created_at=str(doc.get("created_at", "")),
    )


@router.get("", response_model=List[DocumentResponse], summary="List educational documents")
async def list_documents(
    course_id: Optional[int] = Query(default=None, description="Optional filter by course ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns accessible documents based on user role and optional course filter.
    """
    user_id = current_user["id"]
    user_role = current_user["role"]

    if course_id is not None:
        docs = get_documents_by_course(course_id)
    elif user_role == "teacher":
        docs = get_all_documents()
    else:
        docs = get_student_accessible_documents(user_id)

    return [_enrich_document(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentResponse, summary="Get document metadata")
async def get_document_details(
    doc_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Fetches detailed metadata and processing metrics for a document.
    """
    doc = get_document_by_doc_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' was not found.",
        )
    return _enrich_document(doc)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and dynamically process educational PDF/text document",
)
async def upload_document(
    course_id: int = Query(..., description="Target course ID for ingestion"),
    file: UploadFile = File(..., description="PDF or text educational document"),
    current_teacher: Dict[str, Any] = Depends(get_current_teacher),
):
    """
    Processes an uploaded PDF/text document through the complete EduHyperRAG pipeline:
    1. Preprocessing & Dual Chunking (Phase 1)
    2. Concept & Hyperedge Extraction (Phase 2)
    3. Document-specific Hypergraph Building (Phase 3)
    4. ChromaDB Semantic Vector Indexing (Phase 4)
    """
    # 1. Verify target course exists and belongs to instructor
    course = get_course_by_id(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} was not found.",
        )

    if course["teacher_id"] != current_teacher["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload documents to courses you created.",
        )

    # 2. Validate file type
    filename = file.filename or "uploaded_document.pdf"
    suffix = Path(filename).suffix.lower()
    if suffix not in [".pdf", ".txt", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF (.pdf) or text (.txt, .md) file.",
        )

    # 3. Read uploaded bytes
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.exception("Failed reading uploaded file bytes.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading uploaded file: {str(e)}",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 4. Trigger dynamic ingestion service
    try:
        service = DocumentProcessingService()
        result = service.process_uploaded_file(
            file_name=filename,
            file_bytes=file_bytes,
            course_id=course_id,
            uploaded_by=current_teacher["id"],
        )

        return DocumentUploadResponse(
            doc_id=result["doc_id"],
            filename=result["filename"],
            status=result["status"],
            num_chunks=result["num_chunks"],
            num_concepts=result["num_concepts"],
            num_hyperedges=result["num_hyperedges"],
            hypergraph_json_path=result.get("hypergraph_json_path"),
            message="Document successfully processed and indexed into hypergraph and vector store.",
        )

    except Exception as e:
        logger.exception(f"Document ingestion failed for {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}",
        )
