"""
Dynamic Document Processing Service for EduHyperRAG.

Processes any uploaded PDF/text document through:

1. Preprocessing and chunking
2. Concept and relationship extraction
3. Document-specific hypergraph construction
4. Vector indexing into ChromaDB

The pipeline is fully subject-agnostic.
No subject, topic, filename, or document is hard-coded.
"""

import re
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import config
from src.database.models import create_document, update_document_status
from src.extraction.pipeline import ExtractionPipeline
from src.hypergraph.build_hypergraph import EduHypergraphBuilder
from src.preprocessing.pipeline import PreprocessingPipeline
from src.retrieval.semantic_retriever import SemanticRetriever
from src.utils.logger import get_logger


logger = get_logger("document_service")


class DocumentProcessingService:
    """
    Service wrapper that integrates dynamic document uploading
    with the existing EduHyperRAG processing pipeline.
    """

    def __init__(
        self,
        preprocessing_pipeline: Optional[PreprocessingPipeline] = None,
        extraction_pipeline: Optional[ExtractionPipeline] = None,
        hypergraph_builder: Optional[EduHypergraphBuilder] = None,
        semantic_retriever: Optional[SemanticRetriever] = None,
    ):
        self.preprocessing_pipeline = (
            preprocessing_pipeline
            or PreprocessingPipeline()
        )

        self.extraction_pipeline = (
            extraction_pipeline
            or ExtractionPipeline()
        )

        self.hypergraph_builder = (
            hypergraph_builder
            or EduHypergraphBuilder()
        )

        self.semantic_retriever = (
            semantic_retriever
            or SemanticRetriever()
        )

    # =========================================================
    # Filename sanitization
    # =========================================================

    @staticmethod
    def _sanitize_filename(file_name: str) -> str:
        """
        Make an uploaded filename safe for Windows/Linux.

        Removes characters that are invalid in Windows filenames
        and protects against reserved Windows filenames.
        """

        original = Path(file_name)

        stem = original.stem
        suffix = original.suffix

        # -----------------------------------------------------
        # Remove Windows-invalid characters
        # < > : " / \ | ? *
        # -----------------------------------------------------

        stem = re.sub(
            r'[<>:"/\\|?*\x00-\x1F]',
            "_",
            stem,
        )

        # -----------------------------------------------------
        # Remove trailing spaces and dots
        # -----------------------------------------------------

        stem = stem.rstrip(" .")

        if not stem:
            stem = "uploaded_document"

        # -----------------------------------------------------
        # Windows reserved filenames
        # -----------------------------------------------------

        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

        if stem.upper() in reserved_names:
            stem = f"{stem}_file"

        return f"{stem}{suffix}"

    # =========================================================
    # Document ID
    # =========================================================

    @staticmethod
    def _create_document_id(
        file_name: str,
        custom_doc_id: Optional[str] = None,
    ) -> str:
        """
        Create a unique document identifier.

        A UUID is used by default so that multiple documents with
        identical filenames cannot overwrite one another.
        """

        # -----------------------------------------------------
        # Optional custom document ID
        # -----------------------------------------------------

        if custom_doc_id:

            clean_id = re.sub(
                r"[^a-zA-Z0-9_-]",
                "_",
                custom_doc_id,
            ).strip("_")

            if clean_id:
                return clean_id

        # -----------------------------------------------------
        # Default UUID-based document ID
        # -----------------------------------------------------

        return f"doc_{uuid.uuid4().hex}"

    # =========================================================
    # Main document processing pipeline
    # =========================================================

    def process_uploaded_file(
        self,
        file_name: str,
        file_bytes: bytes,
        course_id: int,
        uploaded_by: int,
        custom_doc_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process an uploaded PDF/text document through the
        complete subject-agnostic EduHyperRAG ingestion pipeline.

        Parameters
        ----------
        file_name:
            Original uploaded filename.

        file_bytes:
            Raw bytes of the uploaded file.

        course_id:
            Course to which this document belongs.

        uploaded_by:
            Teacher/user ID who uploaded the document.

        custom_doc_id:
            Optional custom document identifier.

        Returns
        -------
        Dict[str, Any]
            Processing summary containing document ID,
            chunk/concept/hyperedge counts and hypergraph path.
        """

        # =====================================================
        # 1. SAFE FILENAME
        # =====================================================

        safe_file_name = self._sanitize_filename(
            file_name
        )

        # =====================================================
        # 2. UNIQUE DOCUMENT ID
        # =====================================================

        clean_doc_id = self._create_document_id(
            file_name=safe_file_name,
            custom_doc_id=custom_doc_id,
        )

        logger.info(
            f"Starting ingestion for document "
            f"'{clean_doc_id}' from '{file_name}'"
        )

        # =====================================================
        # 3. DOCUMENT STORAGE DIRECTORY
        # =====================================================

        course_raw_dir = (
            config.courses_data_dir
            / str(course_id)
            / "raw"
        )

        course_raw_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        saved_file_path = (
            course_raw_dir
            / safe_file_name
        )

        # =====================================================
        # 4. SAVE UPLOADED FILE
        # =====================================================

        with open(
            saved_file_path,
            "wb",
        ) as f:
            f.write(file_bytes)

        logger.info(
            f"Saved uploaded file to "
            f"{saved_file_path}"
        )

        # =====================================================
        # 5. CREATE DATABASE DOCUMENT RECORD
        # =====================================================

        create_document(
            doc_id=clean_doc_id,
            filename=file_name,
            file_path=str(
                saved_file_path
            ),
            course_id=course_id,
            uploaded_by=uploaded_by,
            status="PROCESSING",
        )

        try:

            # =================================================
            # PHASE 1
            # Preprocessing + Chunking
            # =================================================

            p1_summary = (
    		self.preprocessing_pipeline.process_file(
        		saved_file_path,
        		doc_id=clean_doc_id,
        		course_id=course_id,
        		teacher_id=uploaded_by,
    		)
	)

            semantic_chunks_path = (
                p1_summary[
                    "semantic_chunks_path"
                ]
            )

            logger.info(
                f"Phase 1 completed for "
                f"'{clean_doc_id}'"
            )

            # =================================================
            # PHASE 2
            # Concept / Relationship Extraction
            # =================================================

            p2_summary = (
                self.extraction_pipeline.process_chunks_file(
                    semantic_chunks_path
                )
            )

            extractions_path = (
                p2_summary[
                    "extraction_output_path"
                ]
            )

            logger.info(
                f"Phase 2 completed for "
                f"'{clean_doc_id}'"
            )

            # =================================================
            # PHASE 3
            # DOCUMENT-SPECIFIC HYPERGRAPH
            # =================================================

            (
                concepts_path,
                hyperedges_path,
            ) = (
                self.hypergraph_builder
                .prepare_input_files_from_extractions(
                    extractions_path,
                    doc_id=clean_doc_id,
                )
            )

            # Build only from this document's
            # concepts and hyperedges.
            self.hypergraph_builder.build_from_files(
                concepts_path,
                hyperedges_path,
            )

            # -------------------------------------------------
            # Save ONLY document-specific hypergraph
            # -------------------------------------------------

            doc_hypergraph_json = (
                config.knowledge_base_dir
                / f"hypergraph_{clean_doc_id}.json"
            )

            self.hypergraph_builder.save_hypergraph_json(
                doc_hypergraph_json
            )

            logger.info(
                f"Saved document-specific hypergraph to "
                f"{doc_hypergraph_json}"
            )

            # =================================================
            # PHASE 4
            # ChromaDB Vector Indexing
            # =================================================

            self.semantic_retriever.index_from_file(
                semantic_chunks_path,
                course_id=course_id,
                teacher_id=uploaded_by,
            )

            logger.info(
                f"Vector indexing completed for "
                f"'{clean_doc_id}'"
            )

            # =================================================
            # DATABASE STATUS
            # =================================================

            num_chunks = (
                p1_summary[
                    "semantic_chunks_count"
                ]
            )

            num_concepts = (
                p2_summary[
                    "total_entities"
                ]
            )

            num_hyperedges = (
                p2_summary[
                    "total_high_order_hyperedges"
                ]
                +
                p2_summary[
                    "total_low_order_relations"
                ]
            )

            update_document_status(
                doc_id=clean_doc_id,
                status="READY",
                num_chunks=num_chunks,
                num_concepts=num_concepts,
                num_hyperedges=num_hyperedges,
            )

            logger.info(
                f"Successfully finished ingestion "
                f"for document '{clean_doc_id}'"
            )

            # =================================================
            # RETURN PROCESSING RESULT
            # =================================================

            return {
                "doc_id": clean_doc_id,
                "filename": file_name,
                "status": "READY",
                "num_chunks": num_chunks,
                "num_concepts": num_concepts,
                "num_hyperedges": num_hyperedges,
                "hypergraph_json_path": str(
                    doc_hypergraph_json
                ),
            }

        except Exception as e:

            logger.exception(
                f"Error during document processing "
                f"for '{clean_doc_id}'"
            )

            # -------------------------------------------------
            # Mark document as ERROR
            # -------------------------------------------------

            try:
                update_document_status(
                    doc_id=clean_doc_id,
                    status="ERROR",
                )
            except Exception:
                logger.exception(
                    "Failed to update document "
                    "status to ERROR."
                )

            raise